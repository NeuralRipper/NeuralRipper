import { useState, useEffect, useRef } from "react"
import type { InferenceResultResponse } from "@/types"
import EXAMPLE_RESULTS from "@/components/ExampleResults"

const CHAR_RATE = 40        // characters per second
const TICK_MS = 50          // update interval (~20fps)
const INITIAL_DELAY = 600   // ms before first model starts
const STAGGER_MS = 400      // ms between each model starting
const PAUSE_MS = 3500       // ms to hold after all complete before looping

// Same null shape as useInferenceSocket's "model_start" state
const BLANK_METRICS: Partial<InferenceResultResponse> = {
    response_text: null,
    ttft_ms: null, tpot_ms: null, tokens_per_second: null,
    e2e_latency_ms: null, gpu_utilization_pct: null,
    gpu_memory_used_mb: null, gpu_memory_total_mb: null,
}

export function useDemoAnimation(active: boolean) {
    const [rows, setRows] = useState(EXAMPLE_RESULTS)
    const intervalRef = useRef<ReturnType<typeof setInterval>>()
    const timeoutRef = useRef<ReturnType<typeof setTimeout>>()
    const startRef = useRef(0)

    useEffect(() => {
        if (!active) {
            setRows(EXAMPLE_RESULTS)
            clearInterval(intervalRef.current)
            clearTimeout(timeoutRef.current)
            return
        }

        function startCycle() {
            startRef.current = performance.now()
            clearInterval(intervalRef.current)
            intervalRef.current = setInterval(tick, TICK_MS)
        }

        function tick() {
            const elapsed = performance.now() - startRef.current
            let allDone = true

            const next = EXAMPLE_RESULTS.map((ex, i) => {
                const modelStart = INITIAL_DELAY + i * STAGGER_MS
                const modelElapsed = elapsed - modelStart
                const fullText = ex.result.response_text ?? ""

                // Not started yet — blank metrics, same as live "pending"
                if (modelElapsed < 0) {
                    allDone = false
                    return {
                        name: ex.name,
                        result: { ...ex.result, ...BLANK_METRICS, status: "pending" as const },
                    }
                }

                const charsRevealed = Math.min(
                    fullText.length,
                    Math.floor((modelElapsed * CHAR_RATE) / 1000),
                )

                // Finished typing — return original example as-is
                if (charsRevealed >= fullText.length) {
                    return ex
                }

                // Streaming — use example metrics, just animate text & null out e2e
                allDone = false
                return {
                    name: ex.name,
                    result: {
                        ...ex.result,
                        status: "streaming" as const,
                        response_text: fullText.slice(0, charsRevealed),
                        e2e_latency_ms: null,
                    },
                }
            })

            setRows(next)

            if (allDone) {
                clearInterval(intervalRef.current)
                timeoutRef.current = setTimeout(startCycle, PAUSE_MS)
            }
        }

        startCycle()

        return () => {
            clearInterval(intervalRef.current)
            clearTimeout(timeoutRef.current)
        }
    }, [active])

    return rows
}
