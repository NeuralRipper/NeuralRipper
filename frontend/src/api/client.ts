// Shared fetch wrapper, every API call reuse these funcs
// Handles: base URL, auth header, error throwing, JSON parsing

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000"

// Token lives in localStorage, these helpers keep it in one place
export const getToken = () => localStorage.getItem("token")
export const setToken = (token: string) => localStorage.setItem("token", token)
export const clearToken = () => localStorage.removeItem("token")

// The core wrapper, all REST calls use this
// <T> generic type, compile time only, tells compiler we will return type <xxx>, no worries
export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options?.headers as Record<string, string>,  // unwrap all headers mappings here
  }

  // set token into headers if it is in the local storage
  if (token) {
    headers["Authorization"] = `Bearer ${token}`
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    throw new Error(body?.detail ?? `${response.status} ${response.statusText}`)
  }
  return response.json()   // always return Promise<any> at runtime
}

// WebSocket factory — inference.ts uses this
export function createSocket(path: string): WebSocket {
  return new WebSocket(`${WS_BASE_URL}${path}`)
}
