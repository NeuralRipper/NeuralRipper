import type { InferenceResultResponse } from "@/types"

export default function PromptCard({ result, name, streaming }: {
    result: InferenceResultResponse
    name: string
    streaming?: boolean
}) {
    const done = result.status === "completed"

    return (
        <div className="border border-border bg-card p-3 space-y-1">
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
            <div className="text-sm text-foreground whitespace-pre-wrap">
                {result.response_text ?? (
                    <span className="text-muted-foreground animate-pulse">waiting for response...</span>
                )}
                {streaming && <span className="animate-pulse">|</span>}
            </div>
        </div>
    )
}
