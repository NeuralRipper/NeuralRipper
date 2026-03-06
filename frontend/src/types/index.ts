// 1:1 mirror of backend/schemas/*.py

// auth.py -> UserInfo, TokenResponse
export interface UserInfo {
  id: number
  email: string
  name: string | null
  avatar_url: string | null
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: UserInfo
}

// model.py -> ModelResponse
export interface ModelResponse {
  id: number
  name: string
  hf_model_id: string
  model_type: string
  parameter_count: number | null
  quantization: string
  description: string | null
  is_downloaded: boolean
  vram_gb: number | null
  created_at: string
}

// inference.py -> InferenceCreate, InferenceCreateResponse, InferenceResultResponse, SessionList, SessionDetail
export interface InferenceCreate {
  prompt: string
  model_ids: number[]
  gpu_tier?: string
}

export interface InferenceCreateResponse {
  session_id: number
  result_ids: number[]
}

export interface InferenceResultResponse {
  id: number
  model_id: number
  status: "pending" | "streaming" | "completed" | "failed"
  response_text: string | null
  finish_reason: string | null
  // token counts
  prompt_tokens: number | null
  completion_tokens: number | null
  total_tokens: number | null
  // latency
  ttft_ms: number | null
  tpot_ms: number | null
  tokens_per_second: number | null
  e2e_latency_ms: number | null
  // GPU
  gpu_name: string | null
  gpu_utilization_pct: number | null
  gpu_memory_used_mb: number | null
  gpu_memory_total_mb: number | null
}

export interface SessionListResponse {
  id: number
  user_name: string | null
  user_avatar: string | null
  prompt: string
  model_ids: number[]
  gpu_tier: string
  created_at: string
}

export interface SessionDetailResponse extends SessionListResponse {
  results: InferenceResultResponse[]
}

// WebSocket message (server -> client), single flat type with optional fields per msg type
export interface WsMessage {
  type: "model_start" | "model_loading" | "token" | "model_complete" | "model_error" | "session_complete" | "error"
  model_id?: number
  model_name?: string
  result?: InferenceResultResponse
  message?: string
  delta?: string
}
