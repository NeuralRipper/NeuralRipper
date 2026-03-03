"""
Inference routes:
POST /inference              -> create session + fire Modal tasks
GET  /inference/{id}/stream  -> SSE stream of results
"""

import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.db import get_session
from dependencies.auth import get_current_user
from db.inference_session import InferenceSession
from db.inference_result import InferenceResult
from schemas.inference import InferenceCreate, InferenceCreateResponse, InferenceResultResponse
from handlers.modal import run_modal_inference

router = APIRouter(prefix="/inference")


@router.post("/", response_model=InferenceCreateResponse)
async def create_inference(
    body: InferenceCreate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    """
    1. Create InferenceSession Row
    2. Create N InferenceResult rows (1 per model, all pending)
    3. Fire N Modal tasks (async, return immediately)
    4. Return session_id + result_ids immediately
    """
    # create session (request info -> ORM struct)
    inf_session = InferenceSession(
        user_id=user_id, prompt=body.prompt, model_ids=body.model_ids
    )
    session.add(inf_session)
    await session.commit()
    await session.refresh(inf_session)

    # create pending result for each model (model_id + session_id -> infer_result)
    for model_id in body.model_ids:
        inf_result = InferenceResult(session_id=inf_session.id, model_id=model_id)
        session.add(inf_result)
    await session.commit()

    # reload to get auto-gen IDs
    db_res = await session.execute(
        select(InferenceResult).where(InferenceResult.session_id == inf_session.id)
    )
    results = db_res.scalars().all()
    result_ids = [r.id for r in results]

    # fire Modal tasks — don't await, return immediately
    for r in results:
        asyncio.create_task(run_modal_inference(r.id, r.model_id, body.prompt))

    return InferenceCreateResponse(session_id=inf_session.id, result_ids=result_ids)


@router.get("/{session_id}/stream")
async def stream_results(
    session_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    """
    SSE endpoint (unclosed http connection) polls DB, pushes updates to client
    Client (React) connects with: EventSource("/inference/5/stream")
    """
    async def event_generator():
        completed = set()   # hashset for finished result IDs

        while True:
            # query all inference results for current session
            db_results = await session.execute(
                select(InferenceResult).where(InferenceResult.session_id == session_id)
            )
            results = db_results.scalars().all()

            for r in results:
                if r.status in ("completed", "failed") and r.id not in completed:
                    data = InferenceResultResponse.model_validate(r).model_dump_json()
                    yield f"data: {data}\n\n"
                    completed.add(r.id)
                elif r.status == "streaming" and r.id not in completed:
                    data = InferenceResultResponse.model_validate(r).model_dump_json()
                    yield f"data: {data}\n\n"

            # all done — close the stream
            if len(completed) == len(results):
                yield "event: complete\ndata: {}\n\n"
                break

            await asyncio.sleep(1)  # poll interval

    return StreamingResponse(event_generator(), media_type="text/event-stream")
