import { useState, useEffect, useRef } from "react"
import { useInferenceSocket } from "@/hooks/useInferenceSocket"
import { listModels } from "@/api/models"
import { createSession } from "@/api/inference"
import type { ModelResponse } from "@/types"
import PromptCard from "./PromptCard"
import MetricsTable from "./MetricsTable"
import Charts from "./Charts"
import EXAMPLE_RESULTS from "./ExampleResults"


export default function Playground() {
  const [models, setModels] = useState<ModelResponse[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [prompt, setPrompt] = useState("")
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [submittedPrompt, setSubmittedPrompt] = useState<string | null>(null)
  const cardsRef = useRef<HTMLDivElement>(null)

  const { inferenceResults, isComplete, error } = useInferenceSocket(sessionId)

  useEffect(() => { listModels().then(setModels).catch(console.error) }, [])
  useEffect(() => { cardsRef.current?.scrollTo({ top: cardsRef.current.scrollHeight, behavior: "smooth" }) }, [inferenceResults])

  const toggle = (id: number) =>
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const submit = async () => {
    if (!prompt.trim() || selectedIds.length === 0) return
    setSubmittedPrompt(prompt)
    const res = await createSession({ prompt, model_ids: selectedIds })
    setSessionId(res.session_id)
  }

  const running = sessionId !== null && !isComplete
  const hasResults = inferenceResults.size > 0

  // Build metrics rows from completed results
  const metricsRows = hasResults
    ? Array.from(inferenceResults.entries())
      .filter(([, r]) => r.status === "completed")
      .map(([modelId, result]) => ({
        name: models.find(m => m.id === modelId)?.name ?? `Model ${modelId}`,
        result,
      }))
    : EXAMPLE_RESULTS.map(ex => ({ name: ex.name, result: ex.result }))

  return (
    <div className="min-h-screen bg-background text-foreground p-4">
      <div className="max-w-7xl mx-auto space-y-4">

        {/* Header */}
        <div className="border border-border bg-card px-4 py-3 flex items-center justify-between">
          <span className="text-lg font-bold text-cyan-400">NEURAL RIPPER</span>
          <span className="text-xs text-muted-foreground">LLM EVAL LAB v0.1</span>
        </div>

        {/* Two-panel layout: left prompt cards, right metrics table */}
        <div className="flex gap-4 items-start" style={{ minHeight: "calc(100vh - 120px)" }}>

          {/* Left — Prompt cards + input */}
          <div className="w-1/2 border border-border bg-card flex flex-col" style={{ height: "calc(100vh - 120px)" }}>
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

            {/* Prompt cards scrollable */}
            <div ref={cardsRef} className="flex-1 overflow-y-auto p-3 space-y-3">
              {hasResults
                ? Array.from(inferenceResults.entries()).map(([modelId, result]) => (
                  <PromptCard
                    key={modelId}
                    result={result}
                    name={models.find(m => m.id === modelId)?.name ?? `Model ${modelId}`}
                    streaming={running && result.status !== "completed" && result.status !== "failed"}
                  />
                ))
                : !running && (
                  <>
                    {EXAMPLE_RESULTS.map((ex, i) => (
                      <div key={i} className="opacity-50">
                        <PromptCard result={ex.result} name={ex.name} />
                      </div>
                    ))}
                  </>
                )
              }
              {error && <div className="text-red-400 text-sm">{error}</div>}
              {isComplete && hasResults && !error && (
                <div className="text-center text-xs text-muted-foreground py-2">session complete</div>
              )}
            </div>
            {/* Chat input — pinned to bottom of right panel */}
            <div className="border-t border-border p-3 space-y-2">
              <div className="flex items-start gap-2">
                <span className="text-yellow-400 mt-1">_</span>
                <textarea
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit() } }}
                  disabled={running}
                  rows={2}
                  placeholder="Enter your prompt..."
                  className="flex-1 bg-transparent text-yellow-400 outline-none resize-none placeholder:text-muted-foreground disabled:opacity-50"
                />
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">Shift+Enter for new line</span>
                {running && <span className="text-cyan-400 animate-pulse">RUNNING...</span>}
              </div>
            </div>
          </div>

          {/* Right Metrics table + chat input */}
          <div className="w-1/2 border border-border bg-card flex flex-col" style={{ height: "calc(100vh - 120px)" }}>
            <div className="flex-1 overflow-y-auto p-3 space-y-4">
              <div>
                <div className="text-xs text-muted-foreground font-bold uppercase tracking-wider mb-2">
                  Metrics Comparison
                </div>
                <MetricsTable rows={metricsRows} />
              </div>
              <Charts rows={metricsRows} />
              <div>
                <div className="text-xs text-muted-foreground font-bold uppercase tracking-wider mb-2">
                  Input Prompt
                </div>
                <div className="text-sm text-yellow-400/80 font-mono">
                  {submittedPrompt ?? "Explain quantum computing in simple terms"}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
