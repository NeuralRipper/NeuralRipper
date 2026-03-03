from pydantic import BaseModel, ConfigDict


class InferenceCreate(BaseModel):
    """
    Client send a prompt to create 1 ~ n new inference
    """
    prompt: str     # prompt from client
    model_ids: list[int]    # [2, 5, 3] ids of selected models


class InferenceCreateResponse(BaseModel):
    session_id: int
    result_ids: list[int]   # frontend receives SSE with ids here


class InferenceResultResponse(BaseModel):
    """
    Client fetch inference result from current sesssion
    """
    id: int
    model_id: int
    status: str     # pending | streaming | completed | failed
    response_text: str | None 
    ttft_ms: float | None       # time to first token
    tpot_ms: float | None       # time per output token
    total_tokens: int | None    # total tokens generated
    e2e_latency_ms : float | None
    model_config = ConfigDict(from_attributes=True)   # pydantic -> ORM
    

    