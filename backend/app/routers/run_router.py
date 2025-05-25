from fastapi import APIRouter
from backend.app.handlers.run_handler import RunHandler

handler = RunHandler()
router = APIRouter(prefix="/runs", tags=["run"])


@router.get("/{eid}")
async def list_runs(eid: str):
    """Get all runs for experiment id"""
    return handler.get_run_list(eid=eid)



@router.get("/{rid}")
async def get_run_by_id(rid: str):
    """Get run details by run id"""
    pass