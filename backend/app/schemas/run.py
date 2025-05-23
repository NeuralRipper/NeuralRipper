from pydantic import BaseModel
from typing import Optional, Dict

class Run(BaseModel):
    # One per training
    run_id: str
    experiment_id: str
    status: str     # "FINISHED", "FAILED", etc
    start_time: Optional[int]
    end_time: Optional[int]
    artifact_uri: Optional[str]
    metrics: Dict[str, float]
    params: Dict[str, str]
    tags: Optional[Dict[str, str]]