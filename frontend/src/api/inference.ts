import { request, createSocket, getToken } from "./client"
import type {
  InferenceCreate,
  InferenceCreateResponse,
  SessionListResponse,
  SessionDetailResponse,
} from "@/types"

// POST /inference/  Create session + pending result rows -> MySQL DB
export async function createSession(body: InferenceCreate): Promise<InferenceCreateResponse> {
  return request<InferenceCreateResponse>("/inference/", {
    method: "POST",
    body: JSON.stringify(body),
  })
}

// GET /inference/sessions  Get all sessions(history) for current user
export async function getSessions(): Promise<SessionListResponse[]> {
  return request<SessionListResponse[]>("/inference/sessions")
}

// GET /inference/sessions/{id}   Get all inference results from specific session
export async function getSessionDetail(sessionId: number): Promise<SessionDetailResponse> {
  return request<SessionDetailResponse>(`/inference/sessions/${sessionId}`)
}

// GET /inference/sessions/latest   Recover last session for current user
export async function getLatestSession(): Promise<SessionDetailResponse | null> {
  return request<SessionDetailResponse | null>("/inference/sessions/latest")
}

// WebSocket  Connect and authenticate in one step
// Returns the socket so the hook can attach onmessage/onclose handlers
export function connectInferenceSocket(sessionId: number): WebSocket {
  const ws = createSocket(`/inference/ws/${sessionId}`)
  ws.onopen = () => {
    // First message must be the JWT — backend verifies before running Modal
    ws.send(JSON.stringify({ token: `Bearer ${getToken()}` }))
  }
  return ws
}
