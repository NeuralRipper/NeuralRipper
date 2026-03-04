import { request } from "./client"
import type { ModelResponse } from "@/types"

// GET /models/
export async function listModels(): Promise<ModelResponse[]> {
  return request<ModelResponse[]>("/models/")
}

// GET /models/{id}
export async function getModelById(modelId: number): Promise<ModelResponse> {
  return request<ModelResponse>(`/models/${modelId}`)
}
