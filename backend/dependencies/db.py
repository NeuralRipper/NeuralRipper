"""
DB session dependency for FastAPI endpoints
Grabs engine from app.state, yields one session per request

Connection: TCP pipe to MySQL, pool managed by SQLAlchemy
Session: application level workspace, grab a connection from the pool and do ORM API, session.add/commit/query()
"""

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


async def get_session(request: Request) -> AsyncSession:
    async_session = async_sessionmaker(request.app.state.engine, expire_on_commit=False)
    async with async_session() as session:
        yield session
