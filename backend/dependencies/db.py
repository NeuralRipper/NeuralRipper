"""
DB session dependency, one function for both HTTP routes and WebSocket.

HTTP:      Depends(get_session), FastAPI injects Request automatically
WebSocket: call get_session(websocket) directly, same engine from app.state
"""

from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_session(conn: Request) -> AsyncGenerator[AsyncSession]:  # type: ignore[arg-type]
    """
    Yields a DB session from the engine stored in app.state by main.py lifespan.
    Works for both Request (HTTP) and WebSocket — both have .app.state.engine.

    HTTP route:  session: AsyncSession = Depends(get_session)
    WebSocket:   async for session in get_session(websocket):
    """
    factory = async_sessionmaker(conn.app.state.engine, expire_on_commit=False)
    async with factory() as session:
        yield session
