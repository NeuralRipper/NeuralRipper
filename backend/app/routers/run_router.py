from typing import List
from fastapi import APIRouter
from app.handlers.run_handler import RunHandler
from app.schemas.run import RunResponse
from app.schemas.metric import MetricDetail

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

@router.get("/metric-names/{rid}")
async def get_metric_names(rid: str):
    """Get metric names and final values"""
    return handler.get_metric_names(rid=rid)

@router.get("/metric/{rid}/{metric_name}", response_model=List[MetricDetail])
async def get_single_metric(rid: str, metric_name: str):
    """Get single metric history"""
    return handler.get_single_metric(rid=rid, metric_name=metric_name)
