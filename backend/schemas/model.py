from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ModelResponse(BaseModel):
    id: int
    name: str
    hf_model_id: str
    model_type: str
    parameter_count: int | None
    quantization: str
    description: str | None
    is_downloaded: bool
    vram_gb: int | None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
