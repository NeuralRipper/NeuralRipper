import type { InferenceResultResponse } from "@/types"

export default function PromptCard({ result, name, streaming }: {
    result: InferenceResultResponse
    name: string
    streaming?: boolean
}) {
    const done = result.status === "completed"

    const statusText =
        done ? `completed${result.finish_reason ? ` (${result.finish_reason})` : ""}`
        : result.status === "failed" ? "failed"
        : result.status === "cold_start" ? `cold start (${result.cold_start_elapsed ?? 0}s)`
        : result.response_text ? "streaming..."
        : result.status === "streaming" ? "loading model..."
        : "starting..."

    const statusColor =
        done ? "text-green-400"
        : result.status === "failed" ? "text-red-400"
        : "text-yellow-400"

    return (
        <div className="border border-border bg-card p-3 flex flex-col h-full min-h-0">
            {/* Model name + status */}
            <div className="flex items-center justify-between text-xs shrink-0">
                <span className="text-cyan-400 font-bold">{name}</span>
                <span className={statusColor}>{statusText}</span>
            </div>

            {/* LLM response — scrollable within card */}
            <div className="text-sm text-foreground whitespace-pre-wrap overflow-y-auto flex-1 min-h-0 mt-1">
                {result.response_text ?? (
                    <span className="text-muted-foreground animate-pulse">
                        {result.status === "cold_start"
                            ? `cold starting container... (${result.cold_start_elapsed ?? 0}s)`
                            : result.status === "streaming" ? "loading model..."
                            : "waiting for response..."}
                    </span>
                )}
                {streaming && result.response_text && <span className="animate-pulse">|</span>}
            </div>
        </div>
    )
}
