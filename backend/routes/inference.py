"""
Inference routes:
POST /inference/                    -> create session + result rows (no Modal fire)
GET  /inference/sessions            -> public list of all sessions (Results tab)
GET  /inference/sessions/{id}       -> full session detail with results + metrics
WS   /inference/ws/{session_id}     -> WebSocket: auth, run Modal, push results live
"""

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.db import get_session
from dependencies.auth import get_current_user, decode_jwt
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



# REST endpoints, read from HTTP Headers directly for most info
@router.post("/", response_model=InferenceCreateResponse)
async def create_inference(
    body: InferenceCreate,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user),
):
    """
    Create inference session + N pending result rows.
    Does NOT fire Modal tasks, the WebSocket endpoint handles that.
    Frontend flow: POST here → get session_id → open WebSocket → Modal runs there.
    """
    inf_session = InferenceSession(
        user_id=user_id, prompt=body.prompt, model_ids=body.model_ids
    )
    session.add(inf_session)
    await session.commit()
    await session.refresh(inf_session)

    for model_id in body.model_ids:
        inf_result = InferenceResult(session_id=inf_session.id, model_id=model_id)
        session.add(inf_result)
    await session.commit()

    db_res = await session.execute(
        select(InferenceResult).where(InferenceResult.session_id == inf_session.id)
    )
    results = db_res.scalars().all()
    result_ids = [r.id for r in results]

    return InferenceCreateResponse(session_id=inf_session.id, result_ids=result_ids)


@router.get("/sessions", response_model=list[SessionListResponse])
async def list_sessions(session: AsyncSession = Depends(get_session)):
    """Public list of all inference sessions for the Results tab."""
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
    """Full session detail with all inference results and metrics."""
    inf_session = await session.get(InferenceSession, session_id)
    if not inf_session:
        raise HTTPException(status_code=404, detail="Session not found")

    user = await session.get(User, inf_session.user_id)

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


# WebSocket endpoints, no Headers after first connection, read from raw text
@router.websocket("/ws/{session_id}")
async def inference_ws(websocket: WebSocket, session_id: int):
    """
    WebSocket lifecycle:
    1. Accept connection
    2. Client sends first message: {"token": "Bearer <jwt>"}
    3. Verify JWT → get user_id (close 4001 if invalid)
    4. Load session from DB, verify ownership (close 4004 if not found / not owner)
    5. For each pending result: asyncio.create_task → call Modal → push result via WS
    6. asyncio.gather all tasks
    7. Send {"type": "session_complete"}, close connection

    Why no Depends(get_current_user) here:
    WebSocket has no HTTP headers after the handshake. HTTPBearer reads the
    Authorization header, which doesn't exist on a WS frame. So we authenticate
    manually via the first message, then call decode_jwt() directly (same function
    that get_current_user uses internally).
    """
    await websocket.accept()

    # 1. Authenticate via first message
    try:
        data = await websocket.receive_json()
        raw_token = data.get("token", "")
        token = raw_token.removeprefix("Bearer ").strip()
        user_id = decode_jwt(token)
    except WebSocketDisconnect:
        return
    except Exception:
        await websocket.send_json({"type": "error", "message": "Invalid or expired token"})
        await websocket.close(code=4001, reason="Invalid token")
        return

    if not user_id:
        await websocket.send_json({"type": "error", "message": "Invalid token payload"})
        await websocket.close(code=4001, reason="Invalid token")
        return

    # 2. Load session + verify ownership
    # WebSocket can't use Depends(), so we call get_session(websocket) directly
    # same function, same engine from app.state — just called manually instead of injected
    async for session in get_session(websocket):
        inf_session = await session.get(InferenceSession, session_id)
        if not inf_session or inf_session.user_id != user_id:
            await websocket.send_json({"type": "error", "message": "Session not found"})
            await websocket.close(code=4004, reason="Session not found")
            return

        # load all pending results for current session
        db_res = await session.execute(
            select(InferenceResult).where(InferenceResult.session_id == session_id)
        )
        results = db_res.scalars().all()

        # 3. Run Modal inference concurrently
        # Create coroutine objects(define the tasks), NOT calling(starting) functions yet
        tasks = [
            run_modal_inference(
                result_id=r.id,
                model_id=r.model_id,
                prompt=inf_session.prompt,
                websocket=websocket,
                db_session=session,
            )
            for r in results
        ]

        try:
            # gather takes N coroutines, (Actual start, calls functions)starts all, returns when all are finished
            # similar to join() in threads, each coro call HTTP -> Modal -> Network I/O
            # 1. submits all coroutines to the event loop, starts them
            # 2. waits until ALL of them finished(join())
            await asyncio.gather(*tasks)
        except WebSocketDisconnect:
            return

        # 4. Done
        await websocket.send_json({"type": "session_complete"})
        await websocket.close()
