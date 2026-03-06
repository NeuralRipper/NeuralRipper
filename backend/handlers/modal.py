"""
Handler that bridges our FastAPI backend with Modal GPU tasks.
Streams tokens from Modal → WebSocket in real time.

Flow: WebSocket orchestrates → Modal streams tokens → push to WS + save to DB
"""

import asyncio
import logging
import time
import traceback

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

# Per-chunk timeout: if Modal doesn't yield a chunk within this many seconds, abort
CHUNK_TIMEOUT_SECONDS = 300


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
    4. Push token/metrics_update/model_complete (or model_error) to WebSocket
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

        gen = None
        try:
            import modal

            # Pick GPU class dynamically based on user's tier selection
            class_name = GPU_CLASS_MAP.get(gpu_tier, "ModelA10G")
            ModelCls = modal.Cls.from_name("neuralripper-inference", class_name)
            model_instance = ModelCls(model_name=model.hf_model_id)

            # Consume streaming generator via run_in_executor
            gen = model_instance.generate_stream.remote_gen(
                prompt=prompt, max_tokens=1024, temperature=0.7
            )
            loop = asyncio.get_event_loop()
            completed_ok = False

            # Cold-start heartbeat: send progress while waiting for first chunk
            first_chunk = asyncio.Event()
            cold_start_time = time.monotonic()

            async def heartbeat():
                await asyncio.sleep(5)  # grace period before assuming cold start
                while not first_chunk.is_set():
                    elapsed = round(time.monotonic() - cold_start_time)
                    await websocket.send_json({
                        "type": "model_cold_start",
                        "model_id": model_id,
                        "elapsed_seconds": elapsed,
                    })
                    await asyncio.sleep(3)

            heartbeat_task = asyncio.create_task(heartbeat())

            try:
                while True:
                    # Timeout per chunk — if Modal hangs, we abort
                    chunk = await asyncio.wait_for(
                        loop.run_in_executor(None, lambda: next(gen, None)),
                        timeout=CHUNK_TIMEOUT_SECONDS,
                    )
                    if chunk is None:
                        break

                    if not first_chunk.is_set():
                        first_chunk.set()
                        heartbeat_task.cancel()

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

                    elif stage == "metrics_update":
                        await websocket.send_json({
                            "type": "metrics_update",
                            "model_id": model_id,
                            "metrics": chunk["metrics"],
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
                        try:
                            await db_session.refresh(result)
                            result.status = "completed"
                            for key, value in metrics.items():
                                setattr(result, key, value)
                            await db_session.commit()
                        except Exception as db_err:
                            logger.error(f"DB commit failed after model {model_id} completed: {db_err}")
                        completed_ok = True

            except asyncio.TimeoutError:
                if gen is not None:
                    try:
                        gen.close()
                    except Exception:
                        pass
                logger.error(f"Modal inference timed out for model {model_id} after {CHUNK_TIMEOUT_SECONDS}s")
                await websocket.send_json({
                    "type": "model_error",
                    "model_id": model_id,
                    "model_name": model.name,
                    "message": f"Inference timed out after {CHUNK_TIMEOUT_SECONDS}s",
                })
                await db_session.refresh(result)
                result.status = "failed"
                result.response_text = f"Timed out after {CHUNK_TIMEOUT_SECONDS}s"
                await db_session.commit()
            finally:
                heartbeat_task.cancel()

        except asyncio.CancelledError:
            # Task was cancelled (user pressed Stop) — close remote generator
            if gen is not None:
                try:
                    gen.close()
                except Exception:
                    pass
            logger.info(f"Inference cancelled for model {model_id}")
            await websocket.send_json({
                "type": "model_error",
                "model_id": model_id,
                "model_name": model.name,
                "message": "Cancelled by user",
            })
            await db_session.refresh(result)
            result.status = "failed"
            result.response_text = "Cancelled by user"
            await db_session.commit()

        except Exception as e:
            if completed_ok:
                logger.warning(f"Post-completion error for model {model_id} (ignoring): {e}")
                return
            if gen is not None:
                try:
                    gen.close()
                except Exception:
                    pass
            logger.error(f"Modal inference failed for model {model_id}: {e}\n{traceback.format_exc()}")
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
