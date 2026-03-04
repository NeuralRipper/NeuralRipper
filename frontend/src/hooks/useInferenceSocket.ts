import { connectInferenceSocket } from "@/api/inference"
import { useEffect, useState } from "react"
import type { WsMessage, InferenceResultResponse } from "@/types"

export function useInferenceSocket(sessionId: number | null) {
  // {model_id: infer_result with all metrics}  
  const [inferenceResults, setInferenceResults] = useState<Map<number, InferenceResultResponse>>(new Map())
  const [isComplete, setIsComplete] = useState(false)   // only for current session status

  useEffect(() => {
    if (!sessionId) return

    const ws = connectInferenceSocket(sessionId)
    setIsComplete(false)
    setInferenceResults(new Map())

    // ws.onmessage is a callback function, browser calls it each time a message arrives
    ws.onmessage = (event) => {
      const msg: WsMessage = JSON.parse(event.data)

      switch (msg.type) {
        case "model_start":
          setInferenceResults(prev =>
            new Map(prev).set(msg.model_id, {
              id: 0, model_id: msg.model_id, status: "pending",
              response_text: null, ttft_ms: null, tpot_ms: null,
              tokens_per_second: null, total_tokens: null, e2e_latency_ms: null,
            })
          )
          break
        case "model_complete":
          setInferenceResults(prev =>
            new Map(prev).set(msg.model_id, msg.result)
          )
          break
        case "model_error":
          setInferenceResults(prev => {
            const existing = prev.get(msg.model_id)
            return new Map(prev).set(msg.model_id, { ...existing!, status: "failed" })
          })
          break
        case "session_complete":
          setIsComplete(true)
          break
      }
    }

    ws.onerror = () => setIsComplete(true)

    return () => ws.close()
  }, [sessionId])

  return { inferenceResults, isComplete }
}
