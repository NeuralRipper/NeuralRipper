"""
Model routes:
GET /models        -> list all available models
GET /models/{id}   -> get model detail
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.db import get_session
from db.models import Model
from schemas.model import ModelResponse

router = APIRouter(prefix="/models")


@router.get("/", response_model=list[ModelResponse])
async def list_models(session: AsyncSession = Depends(get_session)):
    """List all models, public, no auth required"""
    result = await session.execute(select(Model).order_by(Model.id))
    return result.scalars().all()


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: int, session: AsyncSession = Depends(get_session)):
    """Get single model detail, public"""
    model = await session.get(Model, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model
