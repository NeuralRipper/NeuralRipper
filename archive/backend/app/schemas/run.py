from typing import Optional, Dict, Any

from pydantic import BaseModel


class RunInfo(BaseModel):
    artifact_uri: Optional[str] = None
    end_time: Optional[int] = None
    experiment_id: Optional[str] = None
    lifecycle_stage: Optional[str] = None
    run_id: Optional[str] = None
    run_name: Optional[str] = None
    start_time: Optional[int] = None
    status: Optional[str] = None
    user_id: Optional[str] = None


class RunData(BaseModel):
    """
    Metrics and Params are dynamically changing based on mlflow logging in the notebook
    """
    metrics: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, Any]] = None


class RunResponse(BaseModel):
    """
    One per training, nested with other BaseModel
    RunResponse:
        RunData -> RunMetrics,
                -> RunParams
        RunInfo
    """
    data: Optional[RunData] = None
    info: Optional[RunInfo] = None


