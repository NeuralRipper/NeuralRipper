from typing import List

from fastapi import APIRouter, status

from backend.app.handlers.run_handler import RunHandler
from backend.app.schemas.run_response import RunResponse

handler = RunHandler()
router = APIRouter(prefix="/runs", tags=["run"])


@router.get(
    "/list/{eid}",
        response_model=List[RunResponse],
        status_code=status.HTTP_200_OK
    )
async def list_runs(eid: str):
    """Get all runs for experiment id"""
    return handler.get_run_list(eid=eid)


# Tell FastAPI to validate, create doc, field-filter, using the model
@router.get(
"/detail/{rid}",
    response_model=RunResponse,
    status_code=status.HTTP_200_OK
)
async def get_run_by_id(rid: str):
    """Get run details by run id"""
    return handler.get_run_by_id(rid=rid)
