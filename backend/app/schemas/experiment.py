from pydantic import BaseModel
from typing import Optional, Dict

class Experiment(BaseModel):
    experiment_id: str
    name: str   # "ResNet18"
    artifact_location: Optional[str]
    lifecycle_stage: str # "active", "deleted", etc
    tags: Optional[dict]




