"""
Handler that bridges our FastAPI backend with Modal GPU tasks.
Called from the WebSocket endpoint: pushes results directly to the client.

New flow (WS):   WebSocket orchestrates → Modal returns → push to WS + save to DB
"""

import logging

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from db.inference_result import InferenceResult
from db.models import Model

logger = logging.getLogger(__name__)


async def run_modal_inference(
    result_id: int,
    model_id: int,
    prompt: str,
    websocket: WebSocket,       # websocket connection for current client
    engine: AsyncEngine,         # each task creates its own session
):
    """
    1. Look up model's hf_model_id from DB
    2. Push model_start to WebSocket
    3. Call Modal's run_inference remotely (runs on GPU)
    4. Push model_complete (or model_error) to WebSocket
    5. Save final result to DB (for Results tab history)

    This runs as one of N concurrent tasks inside asyncio.gather(),
    orchestrated by the WebSocket endpoint.
    Each task owns its own DB session to avoid concurrent commit conflicts.
    """
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as db_session:
        # resolve model name from DB
        db_model_result = await db_session.execute(select(Model).where(Model.id == model_id))
        model = db_model_result.scalar_one_or_none()

        if not model:
            await websocket.send_json({
                "type": "model_error",
                "model_id": model_id,
                "message": "Model not found in database",
            })
            result = await db_session.get(InferenceResult, result_id)
            result.status = "failed"
            result.response_text = "Model not found"
            await db_session.commit()
            return

        # notify client this model is starting
        await websocket.send_json({
            "type": "model_start",
            "model_id": model_id,
            "model_name": model.name,
        })
        result = await db_session.get(InferenceResult, result_id)
        result.status = "streaming"
        await db_session.commit()

        try:
            # Look up the deployed Modal function by app name + function name
            # Requires: `modal deploy evaluation/modal.py` run once beforehand
            import modal
            run_inference = modal.Function.from_name("neuralripper-inference", "run_inference")
            modal_result = run_inference.remote(model.hf_model_id, prompt)

            # fields to persist and push to client
            fields = {
                "response_text": modal_result["response_text"],
                "finish_reason": modal_result["finish_reason"],
                "prompt_tokens": modal_result["prompt_tokens"],
                "completion_tokens": modal_result["completion_tokens"],
                "total_tokens": modal_result["total_tokens"],
                "ttft_ms": modal_result["ttft_ms"],
                "tpot_ms": modal_result["tpot_ms"],
                "tokens_per_second": modal_result["tokens_per_second"],
                "e2e_latency_ms": modal_result["e2e_latency_ms"],
                "gpu_name": modal_result["gpu_name"],
                "gpu_utilization_pct": modal_result["gpu_utilization_pct"],
                "gpu_memory_used_mb": modal_result["gpu_memory_used_mb"],
                "gpu_memory_total_mb": modal_result["gpu_memory_total_mb"],
            }

            # push result to client immediately via WebSocket
            await websocket.send_json({
                "type": "model_complete",
                "model_id": model_id,
                "model_name": model.name,
                "result": {"id": result_id, "model_id": model_id, "status": "completed", **fields},
            })

            # save to DB (for Results tab, historical sessions are queryable)
            await db_session.refresh(result)
            result.status = "completed"
            for key, value in fields.items():
                setattr(result, key, value)
            await db_session.commit()

        except Exception as e:
            logger.error(f"Modal inference failed for model {model_id}: {e}")
            await websocket.send_json({
                "type": "model_error",
                "model_id": model_id,
                "model_name": model.name,
                "message": str(e),
            })
            await db_session.refresh(result)
            result.status = "failed"
            result.response_text = str(e)
            await db_session.commit()
