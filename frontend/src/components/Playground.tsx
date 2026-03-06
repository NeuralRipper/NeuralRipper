import { useState, useEffect, useRef } from "react"
import { GoogleLogin } from "@react-oauth/google"
import { useAuth } from "@/hooks/useAuth"
import { useInferenceSocket } from "@/hooks/useInferenceSocket"
import { listModels } from "@/api/models"
import { createSession } from "@/api/inference"
import type { ModelResponse } from "@/types"
import PromptCard from "./PromptCard"
import MetricsTable from "./MetricsTable"
import Charts from "./Charts"
import EXAMPLE_RESULTS from "./ExampleResults"


const GPU_TIERS = [
  { id: "t4", label: "T4", vram: 16 },
  { id: "a10g", label: "A10G", vram: 24 },
  { id: "a100", label: "A100", vram: 40 },
  { id: "h100", label: "H100", vram: 80 },
] as const

const GPU_VRAM: Record<string, number> = { t4: 16, a10g: 24, a100: 40, h100: 80 }

export default function Playground() {
  const { user, loading, login, logout } = useAuth()
  const [models, setModels] = useState<ModelResponse[]>([])
  const [selectedIds, setSelectedIds] = useState<number[]>([])
  const [prompt, setPrompt] = useState("")
  const [gpuTier, setGpuTier] = useState("a10g")
  const [sessionId, setSessionId] = useState<number | null>(null)
  const [submittedPrompt, setSubmittedPrompt] = useState<string | null>(null)
  const [modelDropdownOpen, setModelDropdownOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const cardsRef = useRef<HTMLDivElement>(null)

  const { inferenceResults, isComplete, error } = useInferenceSocket(sessionId)

  useEffect(() => { listModels().then(setModels).catch(console.error) }, [])
  useEffect(() => { cardsRef.current?.scrollTo({ top: cardsRef.current.scrollHeight, behavior: "smooth" }) }, [inferenceResults])

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setModelDropdownOpen(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  const toggle = (id: number) =>
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])

  const submit = async () => {
    if (!user || !prompt.trim() || selectedIds.length === 0) return
    setSubmittedPrompt(prompt)
    const res = await createSession({ prompt, model_ids: selectedIds, gpu_tier: gpuTier })
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
          <div className="flex items-center gap-3">
            <span className="text-xs text-muted-foreground">LLM EVAL LAB v0.1</span>
            {loading ? null : user ? (
              <div className="flex items-center gap-2">
                {user.avatar_url && (
                  <img src={user.avatar_url} alt="" className="w-6 h-6 rounded-full" />
                )}
                <span className="text-xs text-foreground">{user.name}</span>
                <button onClick={logout} className="text-xs text-muted-foreground hover:text-red-400 cursor-pointer">
                  logout
                </button>
              </div>
            ) : (
              <GoogleLogin
                onSuccess={r => { if (r.credential) login(r.credential) }}
                size="small"
                theme="filled_black"
                shape="pill"
              />
            )}
          </div>
        </div>

        {/* Two-panel layout: left prompt cards, right metrics table */}
        <div className="flex gap-4 items-start" style={{ minHeight: "calc(100vh - 120px)" }}>

          {/* Left — Prompt cards + input */}
          <div className="w-1/2 border border-border bg-card flex flex-col" style={{ height: "calc(100vh - 120px)" }}>
            {/* Model select dropdown */}
            <div className="border-b border-border p-3 text-sm" ref={dropdownRef}>
              <div className="relative">
                <div className="flex items-center">
                  <button
                    onClick={() => setModelDropdownOpen(prev => !prev)}
                    disabled={running}
                    className="flex items-center gap-2 text-cyan-400 hover:text-cyan-300 disabled:opacity-50 cursor-pointer"
                  >
                    <span className="text-muted-foreground">[</span>
                    {selectedIds.length === 0
                      ? "Select Models"
                      : `${selectedIds.length} model${selectedIds.length > 1 ? "s" : ""} selected`}
                    <span className="text-muted-foreground">]</span>
                    <span className="text-xs text-muted-foreground">{modelDropdownOpen ? "▲" : "▼"}</span>
                  </button>
                  <div className="flex items-center gap-1.5 ml-auto">
                    {GPU_TIERS.map(g => (
                      <button
                        key={g.id}
                        onClick={() => setGpuTier(g.id)}
                        disabled={running}
                        className={`px-2 py-0.5 text-xs border cursor-pointer ${
                          gpuTier === g.id
                            ? "border-cyan-400 text-cyan-400 bg-cyan-400/10"
                            : "border-border text-muted-foreground hover:text-foreground"
                        } disabled:opacity-50`}
                      >
                        {g.label}
                        <span className="text-muted-foreground ml-1">{g.vram}G</span>
                      </button>
                    ))}
                  </div>
                </div>
                {modelDropdownOpen && (
                  <div className="absolute top-full left-0 mt-1 z-20 border border-border bg-card min-w-56 py-1">
                    {models.map(m => (
                      <label
                        key={m.id}
                        className="flex items-center gap-3 px-3 py-1.5 cursor-pointer select-none hover:bg-muted/30"
                      >
                        <span
                          className={`w-4 h-4 border flex items-center justify-center text-xs ${
                            selectedIds.includes(m.id)
                              ? "border-cyan-400 bg-cyan-400/20 text-cyan-400"
                              : "border-muted-foreground text-transparent"
                          }`}
                        >
                          ✓
                        </span>
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(m.id)}
                          onChange={() => toggle(m.id)}
                          className="sr-only"
                        />
                        <span className={selectedIds.includes(m.id) ? "text-cyan-400" : "text-muted-foreground"}>
                          {m.name}
                        </span>
                        <span className="text-xs text-muted-foreground ml-auto">{m.quantization}</span>
                        {m.vram_gb != null && m.vram_gb > GPU_VRAM[gpuTier] && (
                          <span className="text-red-400 text-xs font-bold">OOM</span>
                        )}
                      </label>
                    ))}
                  </div>
                )}
              </div>
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
                <span className="text-muted-foreground">
                  {!user ? "Login to submit" : "Shift+Enter for new line"}
                </span>
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
