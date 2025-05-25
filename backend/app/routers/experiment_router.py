"""
models router
return the related BaseModels for both experiment and run which extracted and created by handler.py
"""

from fastapi import APIRouter

from backend.app.handlers.experiment_handler import ExperimentHandler

exp_handler = ExperimentHandler()

# tags for auto doc grouping
router = APIRouter(prefix="/experiments", tags=["experiment"])


@router.get("/")
async def list_experiments():
    """Get all experiments"""
    return exp_handler.get_experiment_list()


@router.get("/{eid}")
async def get_experiment_by_id(eid: str):
    """Get experiment by eid"""
    return exp_handler.get_experiment_by_id(eid=eid)
