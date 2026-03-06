from datetime import datetime
from pydantic import BaseModel, ConfigDict, field_validator

MAX_MODELS_PER_SESSION = 5


class InferenceCreate(BaseModel):
    """Client sends a prompt to create 1~N new inferences"""
    prompt: str
    model_ids: list[int]
    gpu_tier: str = "t4"

    @field_validator("model_ids")
    @classmethod
    def limit_models(cls, v: list[int]) -> list[int]:
        if len(v) > MAX_MODELS_PER_SESSION:
            raise ValueError(f"Maximum {MAX_MODELS_PER_SESSION} models per session")
        if len(v) == 0:
            raise ValueError("At least 1 model required")
        return v


class InferenceCreateResponse(BaseModel):
    session_id: int
    result_ids: list[int]


class InferenceResultResponse(BaseModel):
    """Single model result with metrics"""
    id: int
    model_id: int
    status: str         # pending | streaming | completed | failed
    response_text: str | None
    finish_reason: str | None
    # token counts
    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None
    # latency
    ttft_ms: float | None
    tpot_ms: float | None
    tokens_per_second: float | None
    e2e_latency_ms: float | None
    # GPU
    gpu_name: str | None
    gpu_utilization_pct: int | None
    gpu_memory_used_mb: int | None
    gpu_memory_total_mb: int | None
    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    """For the Results tab — summary of each session"""
    id: int
    user_name: str | None
    user_avatar: str | None
    prompt: str
    model_ids: list[int]
    gpu_tier: str
    created_at: datetime


class SessionDetailResponse(BaseModel):
    """Full session detail with all results"""
    id: int
    user_name: str | None
    user_avatar: str | None
    prompt: str
    model_ids: list[int]
    created_at: datetime
    results: list[InferenceResultResponse]
