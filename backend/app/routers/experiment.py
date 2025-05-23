"""
models router
return the related BaseModels for both experiment and run which extracted and created by handler.py
"""

from fastapi import APIRouter


# tags for auto doc grouping
router = APIRouter(prefix="/models", tags=["models"])


@router.get("/")
async def models_index():
    # get gallery JSON
    return [{"name": "ResNet18"}, {"name": "ResNet50"}]


@router.get("/{mid}")
async def model_details(mid: str):
    # get metadata for detail JSON
    return mid