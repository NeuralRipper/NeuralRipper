"""
Inference routes:
POST /inference              -> create session + fire Modal tasks
GET  /inference/sessions     -> public list of all sessions (for Results tab)
GET  /inference/sessions/{id}-> session detail with all results
GET  /inference/{id}/stream  -> SSE stream of results
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dependencies.db import get_session
from dependencies.auth import get_current_user
from db.inference_session import InferenceSession
from db.inference_result import InferenceResult
from db.user import User
from schemas.inference import (
    InferenceCreate,
    InferenceCreateResponse,
    InferenceResultResponse,
    SessionListResponse,
    SessionDetailResponse,
)
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


@router.get("/sessions", response_model=list[SessionListResponse])
async def list_sessions(session: AsyncSession = Depends(get_session)):
    """
    Public list of all inference sessions, for the Results tab.
    Returns sessions with user info, ordered newest first.
    """
    result = await session.execute(
        select(InferenceSession, User.name, User.avatar_url)
        .join(User, InferenceSession.user_id == User.id)
        .order_by(InferenceSession.created_at.desc())
        .limit(100)
    )
    rows = result.all()
    return [
        SessionListResponse(
            id=row.InferenceSession.id,
            user_name=row.name,
            user_avatar=row.avatar_url,
            prompt=row.InferenceSession.prompt,
            model_ids=row.InferenceSession.model_ids,
            created_at=row.InferenceSession.created_at,
        )
        for row in rows
    ]


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session_detail(
    session_id: int,
    session: AsyncSession = Depends(get_session),
):
    """Full session detail with all inference results and metrics"""
    inf_session = await session.get(InferenceSession, session_id)
    if not inf_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # get user info
    user = await session.get(User, inf_session.user_id)

    # get all results for this session
    db_res = await session.execute(
        select(InferenceResult).where(InferenceResult.session_id == session_id)
    )
    results = db_res.scalars().all()

    return SessionDetailResponse(
        id=inf_session.id,
        user_name=user.name if user else None,
        user_avatar=user.avatar_url if user else None,
        prompt=inf_session.prompt,
        model_ids=inf_session.model_ids,
        created_at=inf_session.created_at,
        results=[InferenceResultResponse.model_validate(r) for r in results],
    )


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
