import { connectInferenceSocket } from "@/api/inference"
import { useEffect, useState } from "react"
import type { WsMessage, InferenceResultResponse } from "@/types"

export function useInferenceSocket(sessionId: number | null) {
  // {model_id: infer_result with all metrics}
  const [inferenceResults, setInferenceResults] = useState<Map<number, InferenceResultResponse>>(new Map())
  const [isComplete, setIsComplete] = useState(false)   // only for current session status
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return

    const ws = connectInferenceSocket(sessionId)
    setIsComplete(false)
    setError(null)
    setInferenceResults(new Map())

    // ws.onmessage is a callback function, browser calls it each time a message arrives
    ws.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data)

      switch (msg.type) {
        case "model_start":
          setInferenceResults(prev =>
            new Map(prev).set(msg.model_id!, {
              id: 0, model_id: msg.model_id!, status: "pending",
              response_text: null, finish_reason: null,
              prompt_tokens: null, completion_tokens: null, total_tokens: null,
              ttft_ms: null, tpot_ms: null, tokens_per_second: null, e2e_latency_ms: null,
              gpu_name: null, gpu_utilization_pct: null, gpu_memory_used_mb: null, gpu_memory_total_mb: null,
            })
          )
          break
        case "model_loading":
          setInferenceResults(prev => {
            const existing = prev.get(msg.model_id!)
            return new Map(prev).set(msg.model_id!, { ...existing!, status: "streaming" })
          })
          break
        case "model_cold_start":
          setInferenceResults(prev => {
            const existing = prev.get(msg.model_id!)
            if (!existing) return prev
            return new Map(prev).set(msg.model_id!, {
              ...existing,
              status: "cold_start",
              cold_start_elapsed: msg.elapsed_seconds,
            })
          })
          break
        case "token":
          setInferenceResults(prev => {
            const existing = prev.get(msg.model_id!)
            if (!existing) return prev
            return new Map(prev).set(msg.model_id!, {
              ...existing,
              status: "streaming",
              response_text: (existing.response_text ?? "") + (msg.delta ?? ""),
            })
          })
          break
        case "metrics_update":
          setInferenceResults(prev => {
            const existing = prev.get(msg.model_id!)
            if (!existing) return prev
            return new Map(prev).set(msg.model_id!, {
              ...existing,
              ...msg.metrics,
            })
          })
          break
        case "model_complete":
          setInferenceResults(prev =>
            new Map(prev).set(msg.model_id!, msg.result!)
          )
          break
        case "model_error":
          setInferenceResults(prev => {
            const existing = prev.get(msg.model_id!)
            return new Map(prev).set(msg.model_id!, { ...existing!, status: "failed" })
          })
          break
        case "session_complete":
          setIsComplete(true)
          break
        case "error":
          setError(msg.message ?? "Connection error")
          setIsComplete(true)
          break
      }
    }

    ws.onerror = () => setIsComplete(true)

    return () => ws.close()
  }, [sessionId])

  return { inferenceResults, isComplete, error }
}
