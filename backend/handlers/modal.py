"""
Handler that bridges our FastAPI backend with Modal GPU tasks.
Streams tokens from Modal → WebSocket in real time.

Flow: WebSocket orchestrates → Modal streams tokens → push to WS + save to DB
"""

import asyncio
import logging

from fastapi import WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from db.inference_result import InferenceResult
from db.models import Model

logger = logging.getLogger(__name__)

GPU_CLASS_MAP = {
    "t4": "ModelT4",
    "a10g": "ModelA10G",
    "a100": "ModelA100",
    "h100": "ModelH100",
}


async def run_modal_inference(
    result_id: int,
    model_id: int,
    prompt: str,
    gpu_tier: str,
    websocket: WebSocket,
    engine: AsyncEngine,
):
    """
    1. Look up model's hf_model_id from DB
    2. Push model_start to WebSocket
    3. Stream from Modal's generate_stream (runs on GPU)
    4. Push token/model_loading/model_complete (or model_error) to WebSocket
    5. Save final result to DB

    This runs as one of N concurrent tasks inside asyncio.gather().
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
            import modal

            # Pick GPU class dynamically based on user's tier selection
            class_name = GPU_CLASS_MAP.get(gpu_tier, "ModelA10G")
            ModelCls = modal.Cls.from_name("neuralripper-inference", class_name)
            model_instance = ModelCls(model_name=model.hf_model_id)

            # Consume streaming generator via run_in_executor
            # remote_gen() returns a sync generator; we wrap each next() call
            # in an executor so it doesn't block the event loop
            gen = model_instance.generate_stream.remote_gen(
                prompt=prompt, max_tokens=512, temperature=0.7
            )
            loop = asyncio.get_event_loop()

            while True:
                chunk = await loop.run_in_executor(None, lambda: next(gen, None))
                if chunk is None:
                    break

                stage = chunk.get("stage")

                if stage == "generating":
                    # Model loaded on GPU, inference starting
                    await websocket.send_json({
                        "type": "model_loading",
                        "model_id": model_id,
                        "model_name": model.name,
                    })

                elif stage == "token":
                    # Stream individual token to client
                    await websocket.send_json({
                        "type": "token",
                        "model_id": model_id,
                        "delta": chunk["delta"],
                    })

                elif stage == "complete":
                    metrics = chunk["metrics"]

                    # Push final result to client
                    await websocket.send_json({
                        "type": "model_complete",
                        "model_id": model_id,
                        "model_name": model.name,
                        "result": {
                            "id": result_id,
                            "model_id": model_id,
                            "status": "completed",
                            **metrics,
                        },
                    })

                    # Save to DB (for Results tab history)
                    await db_session.refresh(result)
                    result.status = "completed"
                    for key, value in metrics.items():
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
