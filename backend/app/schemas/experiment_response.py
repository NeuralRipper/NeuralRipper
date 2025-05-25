from pydantic import BaseModel
from typing import Optional


class ExperimentResponse(BaseModel):
    id: str
    name: str                               # "ResNet18"
    artifact_location: Optional[str]        # gs://bucket-name/xxx
    lifecycle_stage: str                    # "active", "deleted", etc
    tags: Optional[dict]
    creation_time: str
    last_update_time: str
