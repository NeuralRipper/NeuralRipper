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
  created_at: string
}

// inference.py -> InferenceCreate, InferenceCreateResponse, InferenceResultResponse, SessionList, SessionDetail
export interface InferenceCreate {
  prompt: string
  model_ids: number[]
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
  ttft_ms: number | null
  tpot_ms: number | null
  tokens_per_second: number | null
  total_tokens: number | null
  e2e_latency_ms: number | null
}

export interface SessionListResponse {
  id: number
  user_name: string | null
  user_avatar: string | null
  prompt: string
  model_ids: number[]
  created_at: string
}

export interface SessionDetailResponse extends SessionListResponse {
  results: InferenceResultResponse[]
}

// WebSocket messages (server -> client), matches routes/inference.py ws endpoint
export interface WsModelStart {
  type: "model_start"
  model_id: number
  model_name: string
}

export interface WsModelComplete {
  type: "model_complete"
  model_id: number
  result: InferenceResultResponse
}

export interface WsModelError {
  type: "model_error"
  model_id: number
  message: string
}

export interface WsSessionDone {
  type: "session_complete"
}

export type WsMessage = WsModelStart | WsModelComplete | WsModelError | WsSessionDone
