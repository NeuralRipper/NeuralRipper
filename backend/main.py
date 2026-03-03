from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from db.connection import start_engine
from db.base import Base

from routes.auth import router as auth_router
from routes.inference import router as infer_router
from routes.user import router as user_router
from routes.model import router as model_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function for all initialization startups, instances stored in app.state, disposes at shutdown
    """
    engine = start_engine()
    app.state.engine = engine

    # create all tables if they don't exist (replaces init.sql)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield
    await engine.dispose()


app = FastAPI(lifespan=lifespan)

# CORS — allow frontend dev server and production domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://neuralripper.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount all routes to app
app.include_router(auth_router)
app.include_router(infer_router)
app.include_router(user_router)
app.include_router(model_router)


@app.get("/health")
async def health():
    return {"status": "ok"}

# uv run uvicorn main:app --host 0.0.0.0
