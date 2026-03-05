"""
Modal App definition — runs on Modal's GPU cloud
Defines the vLLM inference server that our backend calls remotely
"""

import modal
import time

vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.13.0", "huggingface_hub==0.36.0", "pynvml==12.0.0")
)

app = modal.App("neuralripper-inference")

hf_cache_vol = modal.Volume.from_name("hf-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)


@app.function(
    image=vllm_image,
    gpu="T4",
    timeout=5 * 60,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
def run_inference(hf_model_id: str, prompt: str, max_tokens: int = 512) -> dict:
    """
    Runs on Modal GPU. Called remotely from our backend via .remote()
    Returns dict with response text, latency metrics, token counts, and GPU stats.
    """
    from vllm import LLM, SamplingParams
    import pynvml

    # GPU snapshot before inference
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
    gpu_name = pynvml.nvmlDeviceGetName(handle)
    gpu_memory_total_mb = round(pynvml.nvmlDeviceGetMemoryInfo(handle).total / 1024 / 1024)

    start = time.perf_counter()

    llm = LLM(model=hf_model_id)
    sampling_params = SamplingParams(max_tokens=max_tokens, temperature=0.7)

    ttft_start = time.perf_counter()
    outputs = llm.generate([prompt], sampling_params)
    end = time.perf_counter()

    # GPU snapshot after inference
    util = pynvml.nvmlDeviceGetUtilizationRates(handle)
    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    pynvml.nvmlShutdown()

    result = outputs[0]
    output = result.outputs[0]
    prompt_tokens = len(result.prompt_token_ids)
    completion_tokens = len(output.token_ids)

    e2e_ms = (end - start) * 1000
    ttft_ms = (end - ttft_start) * 1000
    tpot_ms = e2e_ms / completion_tokens if completion_tokens > 0 else 0

    return {
        "response_text": output.text,
        "finish_reason": output.finish_reason,
        # token counts
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        # latency
        "ttft_ms": round(ttft_ms, 2),
        "tpot_ms": round(tpot_ms, 2),
        "tokens_per_second": round(completion_tokens / (e2e_ms / 1000), 2) if e2e_ms > 0 else 0,
        "e2e_latency_ms": round(e2e_ms, 2),
        # GPU
        "gpu_name": gpu_name,
        "gpu_utilization_pct": util.gpu,
        "gpu_memory_used_mb": round(mem_info.used / 1024 / 1024),
        "gpu_memory_total_mb": gpu_memory_total_mb,
    }
