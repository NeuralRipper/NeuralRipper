import { request, setToken } from "./client"
import type { TokenResponse, UserInfo } from "@/types"

// Direct client mapping for backend auth.py
// POST /auth/google Exchange Google credential for JWT
export async function googleLogin(credential: string): Promise<TokenResponse> {
  const data = await request<TokenResponse>("/auth/google", {
    method: "POST",
    body: JSON.stringify({ token: credential }),
  })
  setToken(data.access_token)
  return data
}

// GET /auth/me Validate stored token, get current user
export async function getMe(): Promise<UserInfo> {
  return request<UserInfo>("/auth/me")
}
