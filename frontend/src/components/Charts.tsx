import { useState } from "react"
import type { InferenceResultResponse } from "@/types"

interface ChartRow {
    name: string
    result: InferenceResultResponse
}

type SortDir = "asc" | "desc"

// Muted colors matching the archive terminal aesthetic
const barStyles = {
    ttft: {
        backgroundColor: "rgb(34 211 238 / 0.6)",
    },
    decode: {
        backgroundColor: "rgb(34 211 238 / 0.2)",
        backgroundImage:
            "repeating-linear-gradient(45deg, transparent, transparent 2px, rgb(34 211 238 / 0.15) 2px, rgb(34 211 238 / 0.15) 4px)",
    },
    vram: {
        backgroundColor: "rgb(16 185 129 / 0.5)",
        backgroundImage:
            "repeating-linear-gradient(45deg, transparent, transparent 2px, rgb(16 185 129 / 0.2) 2px, rgb(16 185 129 / 0.2) 4px)",
    },
    gpu: {
        backgroundColor: "rgb(239 68 68 / 0.5)",
        backgroundImage:
            "repeating-linear-gradient(45deg, transparent, transparent 2px, rgb(239 68 68 / 0.2) 2px, rgb(239 68 68 / 0.2) 4px)",
    },
}

export default function Charts({ rows }: { rows: ChartRow[] }) {
    const [latencySort, setLatencySort] = useState<SortDir>("asc")
    const [resourceSort, setResourceSort] = useState<SortDir>("desc")

    if (rows.length === 0) return null

    const latencyRows = [...rows].sort((a, b) => {
        const aVal = a.result.e2e_latency_ms ?? 0
        const bVal = b.result.e2e_latency_ms ?? 0
        return latencySort === "asc" ? aVal - bVal : bVal - aVal
    })

    const resourceRows = [...rows].sort((a, b) => {
        const aVal = a.result.gpu_memory_used_mb ?? 0
        const bVal = b.result.gpu_memory_used_mb ?? 0
        return resourceSort === "asc" ? aVal - bVal : bVal - aVal
    })

    const e2eValues = rows.map(r => r.result.e2e_latency_ms ?? 0)
    const maxE2E = Math.max(...e2eValues)
    const minE2E = Math.min(...e2eValues.filter(v => v > 0))

    const vramValues = rows.map(r => r.result.gpu_memory_used_mb ?? 0)
    const maxVRAM = Math.max(...vramValues)

    return (
        <div className="space-y-5 font-mono text-xs">
            {/* Latency breakdown */}
            <div>
                <div className="flex items-center justify-between mb-2">
                    <span className="text-muted-foreground font-bold uppercase tracking-wider">
                        Latency Breakdown
                    </span>
                    <SortToggle dir={latencySort} onToggle={() => setLatencySort(d => d === "asc" ? "desc" : "asc")} />
                </div>
                <div className="space-y-1.5">
                    {latencyRows.map(r => {
                        const ttft = r.result.ttft_ms ?? 0
                        const e2e = r.result.e2e_latency_ms ?? 0
                        const decode = Math.max(0, e2e - ttft)
                        const ttftPct = maxE2E > 0 ? (ttft / maxE2E) * 100 : 0
                        const decodePct = maxE2E > 0 ? (decode / maxE2E) * 100 : 0
                        const isFastest = e2e > 0 && e2e === minE2E && rows.length > 1
                        const isSlowest = e2e > 0 && e2e === maxE2E && rows.length > 1

                        return (
                            <BarRow key={r.name} label={r.name}>
                                <div className="flex items-center gap-2 flex-1">
                                    <div className="flex flex-1 h-4 border border-cyan-900/40 rounded-sm overflow-hidden">
                                        <div
                                            className="h-full transition-all duration-500"
                                            style={{ width: `${ttftPct}%`, ...barStyles.ttft }}
                                            title={`TTFT: ${ttft.toFixed(0)}ms`}
                                        />
                                        <div
                                            className="h-full transition-all duration-500"
                                            style={{ width: `${decodePct}%`, ...barStyles.decode }}
                                            title={`Decode: ${decode.toFixed(0)}ms`}
                                        />
                                    </div>
                                    <span className="text-muted-foreground whitespace-nowrap">
                                        {e2e.toFixed(0)}ms
                                        {isFastest && <span className="text-emerald-400"> ← fastest</span>}
                                        {isSlowest && <span className="text-red-400/70"> ← slowest</span>}
                                    </span>
                                </div>
                            </BarRow>
                        )
                    })}
                </div>
                <Legend items={[
                    { style: barStyles.ttft, label: "TTFT", tooltip: "Time to First Token — initial response latency" },
                    { style: barStyles.decode, label: "Decode", tooltip: "Token generation time after first token" },
                ]} />
            </div>

            {/* Resource usage */}
            <div>
                <div className="flex items-center justify-between mb-2">
                    <span className="text-muted-foreground font-bold uppercase tracking-wider">
                        Resource Usage
                    </span>
                    <SortToggle dir={resourceSort} onToggle={() => setResourceSort(d => d === "asc" ? "desc" : "asc")} />
                </div>
                <div className="space-y-1.5">
                    {resourceRows.map(r => {
                        const vram = r.result.gpu_memory_used_mb ?? 0
                        const gpu = r.result.gpu_utilization_pct ?? 0
                        const vramPct = maxVRAM > 0 ? (vram / maxVRAM) * 100 : 0

                        return (
                            <BarRow key={r.name} label={r.name}>
                                <div className="flex flex-col gap-1 flex-1">
                                    <div className="flex items-center gap-2">
                                        <div className="flex flex-1 h-3 border border-emerald-900/40 rounded-sm overflow-hidden">
                                            <div
                                                className="h-full transition-all duration-500"
                                                style={{ width: `${vramPct}%`, ...barStyles.vram }}
                                                title={`VRAM: ${vram} MB`}
                                            />
                                        </div>
                                        <span className="text-muted-foreground whitespace-nowrap">{vram} MB</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <div className="flex flex-1 h-3 border border-red-900/40 rounded-sm overflow-hidden">
                                            <div
                                                className="h-full transition-all duration-500"
                                                style={{ width: `${gpu}%`, ...barStyles.gpu }}
                                                title={`GPU: ${gpu}%`}
                                            />
                                        </div>
                                        <span className="text-muted-foreground whitespace-nowrap">{gpu}%</span>
                                    </div>
                                </div>
                            </BarRow>
                        )
                    })}
                </div>
                <Legend items={[
                    { style: barStyles.vram, label: "VRAM", tooltip: "GPU video memory consumed by the model" },
                    { style: barStyles.gpu, label: "GPU", tooltip: "GPU compute utilization during inference" },
                ]} />
            </div>
        </div>
    )
}

function SortToggle({ dir, onToggle }: { dir: SortDir; onToggle: () => void }) {
    return (
        <button onClick={onToggle} className="text-muted-foreground hover:text-foreground cursor-pointer text-[10px]">
            {dir === "asc" ? "▲ asc" : "▼ desc"}
        </button>
    )
}

function BarRow({ label, children }: { label: string; children: React.ReactNode }) {
    return (
        <div className="flex items-center gap-2">
            <span className="w-18 text-right text-cyan-400/80 truncate shrink-0" title={label}>{label}</span>
            {children}
        </div>
    )
}

function Legend({ items }: { items: { style: React.CSSProperties; label: string; tooltip?: string }[] }) {
    return (
        <div className="flex gap-4 text-[10px] text-muted-foreground mt-1.5 ml-20">
            {items.map(item => (
                <span key={item.label} className="flex items-center gap-1 group/legend relative">
                    <span className="inline-block w-3 h-2 rounded-sm border border-white/10" style={item.style} />
                    <span className={item.tooltip ? "border-b border-dotted border-muted-foreground/40" : ""}>
                        {item.label}
                    </span>
                    {item.tooltip && (
                        <div className="absolute hidden group-hover/legend:block bottom-full left-0 mb-1 px-2 py-1 text-[10px] bg-zinc-900 border border-border text-muted-foreground whitespace-nowrap z-50 pointer-events-none">
                            {item.tooltip}
                        </div>
                    )}
                </span>
            ))}
        </div>
    )
}
