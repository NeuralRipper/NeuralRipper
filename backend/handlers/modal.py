"""
Handler that bridges our FastAPI backend with Modal GPU tasks
Called via asyncio.create_task() from the inference route — runs in background
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from db.inference_result import InferenceResult
from db.models import Model
from settings import DATABASE_URL


async def run_modal_inference(result_id: int, model_id: int, prompt: str):
    """
    1. Look up model's hf_model_id from DB
    2. Call Modal's run_inference remotely
    3. Update InferenceResult row with response + metrics

    Note: this runs as a background task (asyncio.create_task), so it needs
    its own DB session — the request session is already closed by now.
    """
    # create a standalone session (request session is gone by now)
    engine = create_async_engine(f"mysql+aiomysql://{DATABASE_URL}")
    async_session = async_sessionmaker(engine, expire_on_commit=False)

    async with async_session() as session:
        # get the HF model id from our models table
        db_model = await session.execute(select(Model).where(Model.id == model_id))
        model = db_model.scalar_one_or_none()
        if not model:
            await _mark_failed(session, result_id, "Model not found")
            await engine.dispose()
            return

        # update status to streaming
        await _update_status(session, result_id, "streaming")

        try:
            # call Modal remotely — this runs on GPU
            from evaluation.modal import run_inference
            modal_result = run_inference.remote(model.hf_model_id, prompt)

            # update DB with results
            result = await session.get(InferenceResult, result_id)
            result.status = "completed"
            result.response_text = modal_result["response_text"]
            result.ttft_ms = modal_result["ttft_ms"]
            result.tpot_ms = modal_result["tpot_ms"]
            result.tokens_per_second = modal_result["tokens_per_second"]
            result.total_tokens = modal_result["total_tokens"]
            result.e2e_latency_ms = modal_result["e2e_latency_ms"]
            await session.commit()

        except Exception as e:
            await _mark_failed(session, result_id, str(e))

    await engine.dispose()


async def _update_status(session: AsyncSession, result_id: int, status: str):
    result = await session.get(InferenceResult, result_id)
    result.status = status
    await session.commit()


async def _mark_failed(session: AsyncSession, result_id: int, error: str):
    result = await session.get(InferenceResult, result_id)
    result.status = "failed"
    result.response_text = error
    await session.commit()
