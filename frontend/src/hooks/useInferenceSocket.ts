import { connectInferenceSocket } from "@/api/inference"
import { useEffect, useRef, useState } from "react"
import type { WsMessage, InferenceResultResponse } from "@/types"

export function useInferenceSocket(sessionId: number | null) {
  const [inferenceResults, setInferenceResults] = useState<Map<number, InferenceResultResponse>>(new Map())
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  // Client-side timing: track when each model started and first token arrived
  const timingRef = useRef<Map<number, { startedAt: number; firstTokenAt?: number; tokenCount: number }>>(new Map())

  const cancel = () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "cancel" }))
    }
    setIsComplete(true)
  }

  const resetSocket = () => {
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }
    setInferenceResults(new Map())
    setIsComplete(false)
    setError(null)
    timingRef.current = new Map()
  }

  useEffect(() => {
    if (!sessionId) return

    const ws = connectInferenceSocket(sessionId)
    wsRef.current = ws
    setIsComplete(false)
    setError(null)
    setInferenceResults(new Map())
    timingRef.current = new Map()

    ws.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data)
      const now = performance.now()

      switch (msg.type) {
        case "model_start":
          timingRef.current.set(msg.model_id!, { startedAt: now, tokenCount: 0 })
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
        case "token": {
          const timing = timingRef.current.get(msg.model_id!)
          if (timing) {
            timing.tokenCount++
            if (!timing.firstTokenAt) {
              timing.firstTokenAt = now
            }
          }
          setInferenceResults(prev => {
            const existing = prev.get(msg.model_id!)
            if (!existing) return prev
            // Compute client-side live metrics
            const liveMetrics: Partial<InferenceResultResponse> = {}
            if (timing?.firstTokenAt) {
              liveMetrics.ttft_ms = existing.ttft_ms ?? (timing.firstTokenAt - timing.startedAt)
              const elapsed = (now - timing.firstTokenAt) / 1000
              if (elapsed > 0 && timing.tokenCount > 1) {
                liveMetrics.tokens_per_second = existing.tokens_per_second ?? (timing.tokenCount / elapsed)
              }
              liveMetrics.e2e_latency_ms = existing.e2e_latency_ms ?? (now - timing.startedAt)
            }
            return new Map(prev).set(msg.model_id!, {
              ...existing,
              ...liveMetrics,
              status: "streaming",
              response_text: (existing.response_text ?? "") + (msg.delta ?? ""),
            })
          })
          break
        }
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
            return new Map(prev).set(msg.model_id!, {
              ...existing!,
              status: msg.status === "cancelled" ? "cancelled" : "failed",
              response_text: existing?.response_text ?? msg.message ?? null,
            })
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

    return () => {
      ws.close()
      wsRef.current = null
    }
  }, [sessionId])

  return { inferenceResults, isComplete, error, cancel, resetSocket }
}
