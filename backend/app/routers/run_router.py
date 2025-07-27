from typing import List
from fastapi import APIRouter, status
from app.handlers.run_handler import RunHandler
from app.schemas.run import RunResponse
from app.schemas.metric import MetricList

handler = RunHandler()
router = APIRouter(prefix="/runs", tags=["mlflow"])

@router.get("/list/{eid}", response_model=List[RunResponse])
async def list_runs(eid: str):
    """Get all runs for experiment"""
    return handler.get_run_list(eid=eid)

@router.get("/detail/{rid}", response_model=RunResponse)
async def get_run_by_id(rid: str):
    """Get run details"""
    return handler.get_run_by_id(rid=rid)

@router.get("/metrics/{rid}", response_model=MetricList)
async def get_metrics_by_id(rid: str):
    """Get metrics with sampling optimization"""
    return handler.get_metrics_by_id(rid=rid)