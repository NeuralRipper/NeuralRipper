"""
Modal App definition — runs on Modal's GPU cloud
Defines the vLLM inference server that our backend calls remotely
"""

import modal

vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm==0.13.0", "huggingface_hub==0.36.0")
)

app = modal.App("neuralripper-inference")

hf_cache_vol = modal.Volume.from_name("hf-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)


@app.function(
    image=vllm_image,
    gpu="A10G",
    timeout=5 * 60,
    volumes={
        "/root/.cache/huggingface": hf_cache_vol,
        "/root/.cache/vllm": vllm_cache_vol,
    },
)
def run_inference(hf_model_id: str, prompt: str, max_tokens: int = 512) -> dict:
    """
    Runs on Modal GPU. Called remotely from our backend via .remote()
    Returns: {"response_text": ..., "ttft_ms": ..., "tpot_ms": ..., "total_tokens": ..., "e2e_latency_ms": ...}
    """
    import time
    from vllm import LLM, SamplingParams

    start = time.perf_counter()

    llm = LLM(model=hf_model_id)
    sampling_params = SamplingParams(max_tokens=max_tokens, temperature=0.7)

    ttft_start = time.perf_counter()
    outputs = llm.generate([prompt], sampling_params)
    end = time.perf_counter()

    result = outputs[0]
    response_text = result.outputs[0].text
    total_tokens = len(result.outputs[0].token_ids)

    e2e_ms = (end - start) * 1000
    ttft_ms = (end - ttft_start) * 1000  # approximate, vLLM batches internally
    tpot_ms = e2e_ms / total_tokens if total_tokens > 0 else 0

    return {
        "response_text": response_text,
        "ttft_ms": round(ttft_ms, 2),
        "tpot_ms": round(tpot_ms, 2),
        "tokens_per_second": round(total_tokens / (e2e_ms / 1000), 2) if e2e_ms > 0 else 0,
        "total_tokens": total_tokens,
        "e2e_latency_ms": round(e2e_ms, 2),
    }
