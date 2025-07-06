from typing import List

from fastapi import APIRouter, status

from app.handlers.run_handler import RunHandler
from app.schemas.metric import MetricList, MetricDetail
from app.schemas.run import RunResponse
from mlflow.exceptions import RestException

handler = RunHandler()
router = APIRouter(prefix="/runs", tags=["run"])


@router.get("/list/{eid}", response_model=List[RunResponse], status_code=status.HTTP_200_OK)
async def list_runs(eid: str):
    """Get all runs for experiment id"""
    return handler.get_run_list(eid=eid)


# Tell FastAPI to validate, create doc, field-filter, using the model
@router.get("/detail/{rid}", response_model=RunResponse, status_code=status.HTTP_200_OK)
async def get_run_by_id(rid: str):
    """Get run details by run id, overview data of a run"""
    return handler.get_run_by_id(rid=rid)


@router.get("/metrics/{rid}", response_model=MetricList, status_code=status.HTTP_200_OK)
async def get_all_metrics_by_id(rid: str):
    """Get metrics by run id"""
    try:
        run = handler.get_run_by_id(rid)                                    # Get Mlflow Run object
        metric_names = [metric for metric in run.data.metrics.keys()]       # Extract all metric names

        # go through each metric name and get its history
        all_metrics = []
        for metric_name in metric_names:
            metric_history = handler.get_metric_history_by_id(rid=rid, key=metric_name)

            # convert all metrics into MetricDetail BaseModel
            for metric_point in metric_history:
                metric_detail = MetricDetail(
                    key=metric_name,
                    value=metric_point.value,
                    timestamp=metric_point.timestamp,
                    step=metric_point.step,
                    run_id=rid
                )
                all_metrics.append(metric_detail)

        # wrap the result into MetricList
        return MetricList(metrics=all_metrics)

    except RestException as e:
        print(f"Run {rid} not exists, error: {e}")
        return None
