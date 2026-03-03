from datetime import datetime
from pydantic import BaseModel, ConfigDict


class InferenceCreate(BaseModel):
    """Client sends a prompt to create 1~N new inferences"""
    prompt: str
    model_ids: list[int]


class InferenceCreateResponse(BaseModel):
    session_id: int
    result_ids: list[int]


class InferenceResultResponse(BaseModel):
    """Single model result with metrics"""
    id: int
    model_id: int
    status: str         # pending | streaming | completed | failed
    response_text: str | None
    ttft_ms: float | None
    tpot_ms: float | None
    tokens_per_second: float | None
    total_tokens: int | None
    e2e_latency_ms: float | None
    model_config = ConfigDict(from_attributes=True)


class SessionListResponse(BaseModel):
    """For the Results tab — summary of each session"""
    id: int
    user_name: str | None
    user_avatar: str | None
    prompt: str
    model_ids: list[int]
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
