import type { InferenceResultResponse } from "@/types"

// Example data shown to new / logged-out users
export const EXAMPLE_RESULTS: { name: string; result: InferenceResultResponse }[] = [
  {
    name: "Qwen2.5-0.5B",
    result: {
      id: 0, model_id: 1, status: "completed", finish_reason: "stop",
      response_text: "Quantum computing uses qubits instead of classical bits. While a classical bit is either 0 or 1, a qubit can exist in a superposition of both states simultaneously, enabling massive parallelism for certain computations.",
      prompt_tokens: 8, completion_tokens: 42, total_tokens: 50,
      ttft_ms: 245, tpot_ms: 12.3, tokens_per_second: 81.3, e2e_latency_ms: 762,
      gpu_name: "NVIDIA A10G", gpu_utilization_pct: 87, gpu_memory_used_mb: 4821, gpu_memory_total_mb: 23028,
    },
  },
  {
    name: "Llama-3.2-1B",
    result: {
      id: 0, model_id: 2, status: "completed", finish_reason: "stop",
      response_text: "In simple terms, quantum computing harnesses the strange behavior of particles at the quantum level. Unlike regular computers that process one calculation at a time, quantum computers can explore many solutions at once.",
      prompt_tokens: 8, completion_tokens: 39, total_tokens: 47,
      ttft_ms: 312, tpot_ms: 18.7, tokens_per_second: 53.5, e2e_latency_ms: 1041,
      gpu_name: "NVIDIA A10G", gpu_utilization_pct: 94, gpu_memory_used_mb: 8192, gpu_memory_total_mb: 23028,
    },
  },
  {
    name: "Phi-3-mini",
    result: {
      id: 0, model_id: 3, status: "completed", finish_reason: "stop",
      response_text: "Think of a regular computer as someone who reads a book one page at a time. A quantum computer reads all pages at once. This is possible because quantum bits can be 0 and 1 at the same time — a property called superposition.",
      prompt_tokens: 8, completion_tokens: 47, total_tokens: 55,
      ttft_ms: 189, tpot_ms: 9.8, tokens_per_second: 102.1, e2e_latency_ms: 650,
      gpu_name: "NVIDIA A10G", gpu_utilization_pct: 82, gpu_memory_used_mb: 6144, gpu_memory_total_mb: 23028,
    },
  },
]

export default function ResultCard({ result, name, streaming }: {
  result: InferenceResultResponse
  name: string
  streaming?: boolean
}) {
  const done = result.status === "completed"

  return (
    <div className="border border-border bg-card p-3 space-y-2">
      {/* Model name + status */}
      <div className="flex items-center justify-between text-xs">
        <span className="text-cyan-400 font-bold">{name}</span>
        <span className={
          done ? "text-green-400" :
          result.status === "failed" ? "text-red-400" :
          "text-yellow-400"
        }>
          {streaming ? "streaming..." : result.status}
          {done && result.finish_reason && ` (${result.finish_reason})`}
        </span>
      </div>

      {/* LLM response */}
      <div className="text-sm text-foreground min-h-15 whitespace-pre-wrap">
        {result.response_text ?? (
          <span className="text-muted-foreground animate-pulse">waiting for response...</span>
        )}
        {streaming && <span className="animate-pulse">|</span>}
      </div>

      {/* Metrics — two rows */}
      {done && (
        <div className="border-t border-border pt-2 space-y-1 text-xs text-muted-foreground">
          {/* Latency + tokens */}
          <div className="grid grid-cols-3 gap-x-4">
            <span>TTFT: <V>{result.ttft_ms?.toFixed(0) ?? "-"}ms</V></span>
            <span>TPOT: <V>{result.tpot_ms?.toFixed(1) ?? "-"}ms</V></span>
            <span>E2E: <V>{result.e2e_latency_ms?.toFixed(0) ?? "-"}ms</V></span>
            <span>Speed: <V>{result.tokens_per_second?.toFixed(1) ?? "-"} tok/s</V></span>
            <span>Prompt: <V>{result.prompt_tokens ?? "-"}</V></span>
            <span>Completion: <V>{result.completion_tokens ?? "-"}</V></span>
          </div>
          {/* GPU */}
          {result.gpu_name && (
            <div className="grid grid-cols-3 gap-x-4">
              <span>GPU: <V>{result.gpu_name}</V></span>
              <span>Util: <V>{result.gpu_utilization_pct ?? "-"}%</V></span>
              <span>VRAM: <V>{result.gpu_memory_used_mb ?? "-"}/{result.gpu_memory_total_mb ?? "-"} MB</V></span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Yellow value text
function V({ children }: { children: React.ReactNode }) {
  return <span className="text-yellow-400">{children}</span>
}
