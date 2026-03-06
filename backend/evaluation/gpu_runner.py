"""
Modal App definition — runs on Modal's GPU cloud
Defines vLLM inference classes with real token streaming + 4 GPU tiers.
Deploy: cd backend && uv run modal deploy evaluation/gpu_runner.py
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

VOLUMES = {
    "/root/.cache/huggingface": hf_cache_vol,
    "/root/.cache/vllm": vllm_cache_vol,
}

METRICS_INTERVAL = 0.5  # seconds between streaming metrics updates


def _make_gpu_cls(gpu: str):
    """Factory: creates a Modal class for a specific GPU tier with full vLLM streaming."""

    class ModalClass:
        model_name: str = modal.parameter()

        @modal.enter(snap=True)
        def preload(self):
            """Pre-import heavy modules on CPU — captured in memory snapshot."""
            import torch  # noqa: F401
            import vllm  # noqa: F401
            from huggingface_hub import snapshot_download
            snapshot_download(self.model_name)

        @modal.enter(snap=False)
        async def load_engine(self):
            """Initialize vLLM engine on GPU — runs after snapshot restore."""
            from vllm.engine.arg_utils import AsyncEngineArgs
            from vllm.engine.async_llm_engine import AsyncLLMEngine
            import pynvml

            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            self._gpu_name = pynvml.nvmlDeviceGetName(handle)
            self._gpu_memory_total_mb = round(
                pynvml.nvmlDeviceGetMemoryInfo(handle).total / 1024 / 1024
            )
            pynvml.nvmlShutdown()

            engine_args = AsyncEngineArgs(
                model=self.model_name,
                gpu_memory_utilization=0.9,
                max_model_len=4096,
                trust_remote_code=True,
            )
            self.engine = AsyncLLMEngine.from_engine_args(engine_args)

        @modal.method()
        async def generate_stream(
            self, prompt: str, max_tokens: int = 512, temperature: float = 0.7
        ):
            """
            Async generator yielding structured chunks:
              1. {"stage": "generating"}                    — model loaded, starting inference
              2. {"stage": "token", "delta": ...}           — each new token
              3. {"stage": "metrics_update", "metrics": {}} — periodic running metrics
              4. {"stage": "complete", "metrics": {}}       — final metrics + GPU stats
            """
            from vllm import SamplingParams
            import pynvml
            import uuid

            yield {"stage": "generating"}

            sampling_params = SamplingParams(
                max_tokens=max_tokens,
                temperature=temperature,
            )

            request_id = str(uuid.uuid4())
            start = time.perf_counter()
            ttft = None
            previous_text = ""
            prompt_tokens = 0
            completion_tokens = 0
            finish_reason = "unknown"
            last_metrics_time = start

            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)

            try:
                async for output in self.engine.generate(
                    request_id=request_id,
                    prompt=prompt,
                    sampling_params=sampling_params,
                ):
                    current_text = output.outputs[0].text
                    delta = current_text[len(previous_text):]
                    if delta:
                        if ttft is None:
                            ttft = time.perf_counter() - start
                        yield {"stage": "token", "delta": delta}
                    previous_text = current_text

                    # Periodic metrics update (~every 500ms)
                    now = time.perf_counter()
                    if ttft is not None and now - last_metrics_time >= METRICS_INTERVAL:
                        elapsed = now - start
                        n = len(output.outputs[0].token_ids)
                        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                        yield {
                            "stage": "metrics_update",
                            "metrics": {
                                "ttft_ms": round(ttft * 1000, 2),
                                "tpot_ms": round(
                                    ((elapsed - ttft) / max(n - 1, 1)) * 1000, 2
                                ),
                                "tokens_per_second": round(n / elapsed, 2),
                                "e2e_latency_ms": round(elapsed * 1000, 2),
                                "gpu_utilization_pct": util.gpu,
                                "gpu_memory_used_mb": round(mem.used / 1024 / 1024),
                                "completion_tokens": n,
                            },
                        }
                        last_metrics_time = now

                    if output.finished:
                        if (
                            hasattr(output, "prompt_token_ids")
                            and output.prompt_token_ids
                        ):
                            prompt_tokens = len(output.prompt_token_ids)
                        completion_tokens = len(output.outputs[0].token_ids)
                        finish_reason = output.outputs[0].finish_reason or "unknown"

                end = time.perf_counter()
                e2e_ms = (end - start) * 1000
                ttft_ms = (ttft or 0) * 1000
                tpot_ms = (
                    (e2e_ms - ttft_ms) / (completion_tokens - 1)
                    if completion_tokens > 1
                    else 0
                )

                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                yield {
                    "stage": "complete",
                    "metrics": {
                        "response_text": previous_text,
                        "finish_reason": finish_reason,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens,
                        "ttft_ms": round(ttft_ms, 2),
                        "tpot_ms": round(tpot_ms, 2),
                        "tokens_per_second": (
                            round(completion_tokens / (e2e_ms / 1000), 2)
                            if e2e_ms > 0
                            else 0
                        ),
                        "e2e_latency_ms": round(e2e_ms, 2),
                        "gpu_name": self._gpu_name,
                        "gpu_utilization_pct": util.gpu,
                        "gpu_memory_used_mb": round(mem_info.used / 1024 / 1024),
                        "gpu_memory_total_mb": self._gpu_memory_total_mb,
                    },
                }
            finally:
                pynvml.nvmlShutdown()

    # Set class name BEFORE app.cls registers it
    ModalClass.__name__ = f"Model{gpu}"
    ModalClass.__qualname__ = f"Model{gpu}"

    return app.cls(
        gpu=gpu,
        image=vllm_image,
        enable_memory_snapshot=True,
        scaledown_window=900,
        volumes=VOLUMES,
        secrets=[modal.Secret.from_name("huggingface")],
        timeout=5 * 60,
    )(ModalClass)


ModelT4 = _make_gpu_cls("T4")
ModelA10G = _make_gpu_cls("A10G")
ModelA100 = _make_gpu_cls("A100")
ModelH100 = _make_gpu_cls("H100")
