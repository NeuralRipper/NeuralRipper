import type { InferenceResultResponse } from "@/types";

// Example data shown to new / logged-out users
const EXAMPLE_RESULTS: { name: string; result: InferenceResultResponse }[] = [
    {
        name: "Qwen2.5-0.5B",
        result: {
            id: 0, model_id: 1, status: "completed", finish_reason: "stop",
            response_text: "Quantum computing uses qubits that exist in superposition, enabling massive parallelism for certain computations.",
            prompt_tokens: 8, completion_tokens: 20, total_tokens: 28,
            ttft_ms: 245, tpot_ms: 12.3, tokens_per_second: 81.3, e2e_latency_ms: 762,
            gpu_name: "NVIDIA A10G", gpu_utilization_pct: 87, gpu_memory_used_mb: 4821, gpu_memory_total_mb: 23028,
        },
    },
    {
        name: "Llama-3.2-1B",
        result: {
            id: 0, model_id: 2, status: "completed", finish_reason: "stop",
            response_text: "Quantum computing harnesses quantum mechanics to explore many solutions at once, unlike classical one-at-a-time processing.",
            prompt_tokens: 8, completion_tokens: 22, total_tokens: 30,
            ttft_ms: 312, tpot_ms: 18.7, tokens_per_second: 53.5, e2e_latency_ms: 1041,
            gpu_name: "NVIDIA A10G", gpu_utilization_pct: 94, gpu_memory_used_mb: 8192, gpu_memory_total_mb: 23028,
        },
    },
    {
        name: "Phi-3-mini",
        result: {
            id: 0, model_id: 3, status: "completed", finish_reason: "stop",
            response_text: "A quantum computer reads all pages at once using superposition — qubits can be 0 and 1 simultaneously.",
            prompt_tokens: 8, completion_tokens: 19, total_tokens: 27,
            ttft_ms: 189, tpot_ms: 9.8, tokens_per_second: 102.1, e2e_latency_ms: 650,
            gpu_name: "NVIDIA A10G", gpu_utilization_pct: 82, gpu_memory_used_mb: 6144, gpu_memory_total_mb: 23028,
        },
    },
    {
        name: "Gemma-2-2B",
        result: {
            id: 0, model_id: 4, status: "completed", finish_reason: "stop",
            response_text: "Like a spinning coin that's both heads and tails, qubits exist in multiple states to solve problems faster.",
            prompt_tokens: 8, completion_tokens: 20, total_tokens: 28,
            ttft_ms: 278, tpot_ms: 14.2, tokens_per_second: 70.4, e2e_latency_ms: 860,
            gpu_name: "NVIDIA A10G", gpu_utilization_pct: 89, gpu_memory_used_mb: 5632, gpu_memory_total_mb: 23028,
        },
    },
    {
        name: "Mistral-7B",
        result: {
            id: 0, model_id: 5, status: "completed", finish_reason: "stop",
            response_text: "Qubits leverage superposition and entanglement for exponential speedups in cryptography and optimization tasks.",
            prompt_tokens: 8, completion_tokens: 17, total_tokens: 25,
            ttft_ms: 421, tpot_ms: 22.1, tokens_per_second: 45.2, e2e_latency_ms: 1395,
            gpu_name: "NVIDIA A10G", gpu_utilization_pct: 97, gpu_memory_used_mb: 14336, gpu_memory_total_mb: 23028,
        },
    },
]

export default EXAMPLE_RESULTS;