import { useState, useEffect, useRef } from "react"
import { useInferenceSocket } from "@/hooks/useInferenceSocket"
import { listModels } from "@/api/models"
import { createSession } from "@/api/inference"
import type { ModelResponse } from "@/types"
import ResultCard, { EXAMPLE_RESULTS } from "./ResultCard"

export default function Playground() {
  const [models, setModels] = useState<ModelResponse[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [prompt, setPrompt] = useState("")
  const [sessionId, setSessionId] = useState<number | null>(null)
  const resultsRef = useRef<HTMLDivElement>(null)

  const { inferenceResults, isComplete, error } = useInferenceSocket(sessionId)

  useEffect(() => { listModels().then(setModels).catch(console.error) }, [])
  useEffect(() => { resultsRef.current?.scrollTo({ top: resultsRef.current.scrollHeight, behavior: "smooth" }) }, [inferenceResults])

  const toggle = (id: number) =>
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const submit = async () => {
    if (!prompt.trim() || selectedIds.length === 0) return
    const res = await createSession({ prompt, model_ids: selectedIds })
    setSessionId(res.session_id)
  }

  const running = sessionId !== null && !isComplete
  const hasResults = inferenceResults.size > 0

  return (
    <div className="min-h-screen bg-background text-foreground p-4">
      <div className="max-w-7xl mx-auto space-y-4">

        {/* Header */}
        <div className="border border-border bg-card px-4 py-3 flex items-center justify-between">
          <span className="text-lg font-bold text-cyan-400">NEURAL RIPPER</span>
          <span className="text-xs text-muted-foreground">LLM EVAL LAB v0.1</span>
        </div>

        {/* Two-panel layout: left chat, right results */}
        <div className="flex gap-4 items-start" style={{ minHeight: "calc(100vh - 120px)" }}>

          {/* Left — Chat box */}
          <div className="w-2/5 border border-border bg-card flex flex-col" style={{ height: "calc(100vh - 120px)" }}>
            {/* Model select */}
            <div className="border-b border-border p-3 flex flex-wrap gap-3 text-sm">
              {models.map(m => (
                <label key={m.id} className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={selectedIds.includes(m.id)}
                    onChange={() => toggle(m.id)}
                    disabled={running}
                    className="accent-cyan-400"
                  />
                  <span className={selectedIds.includes(m.id) ? "text-cyan-400" : "text-muted-foreground"}>
                    {m.name}
                  </span>
                </label>
              ))}
            </div>

            {/* Chat area — grows to fill */}
            <div className="flex-1 overflow-y-auto p-3 text-sm text-muted-foreground">
              {!hasResults && !running && (
                <span>Select models and enter a prompt to begin.</span>
              )}
              {error && <div className="text-red-400">{error}</div>}
            </div>

            {/* Prompt input — pinned to bottom */}
            <div className="border-t border-border p-3 flex items-center gap-2">
              <span className="text-yellow-400">{">"}</span>
              <input
                type="text"
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                onKeyDown={e => e.key === "Enter" && submit()}
                disabled={running}
                placeholder="Enter your prompt..."
                className="flex-1 bg-transparent text-yellow-400 outline-none placeholder:text-muted-foreground disabled:opacity-50"
              />
              {running && <span className="text-cyan-400 text-xs animate-pulse">RUNNING...</span>}
            </div>
          </div>

          {/* Right — Stacked result cards */}
          <div ref={resultsRef} className="w-3/5 space-y-3 overflow-y-auto" style={{ maxHeight: "calc(100vh - 120px)" }}>
            {hasResults
              ? Array.from(inferenceResults.entries()).map(([modelId, result]) => (
                  <ResultCard
                    key={modelId}
                    result={result}
                    name={models.find(m => m.id === modelId)?.name ?? `Model ${modelId}`}
                    streaming={running && result.status !== "completed" && result.status !== "failed"}
                  />
                ))
              : /* Example data for new / logged-out users */
                EXAMPLE_RESULTS.map((ex, i) => (
                  <div key={i} className="opacity-50">
                    <ResultCard result={ex.result} name={ex.name} />
                  </div>
                ))
            }
            {isComplete && hasResults && !error && (
              <div className="text-center text-xs text-muted-foreground py-2">session complete</div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
