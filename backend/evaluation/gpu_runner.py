"""
Modal App definition — runs on Modal's GPU cloud.
Defines vLLM inference classes with real token streaming + 4 GPU tiers.

Uses vLLM subprocess + sleep mode for GPU memory snapshots (~5s cold starts).
Deploy: cd backend && uv run modal deploy evaluation/gpu_runner.py
"""

import modal
import time
import socket
import subprocess

VLLM_PORT = 8000
METRICS_INTERVAL = 0.5  # seconds between streaming metrics updates

vllm_image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install(
        "vllm==0.13.0", "huggingface_hub==0.36.0", "pynvml==12.0.0", "aiohttp"
    )
    .env({
        "VLLM_SERVER_DEV_MODE": "1",
        "TORCHINDUCTOR_COMPILE_THREADS": "1",
        "HF_XET_HIGH_PERFORMANCE": "1",
    })
)

app = modal.App("neuralripper-inference")

hf_cache_vol = modal.Volume.from_name("hf-cache", create_if_missing=True)
vllm_cache_vol = modal.Volume.from_name("vllm-cache", create_if_missing=True)

VOLUMES = {
    "/root/.cache/huggingface": hf_cache_vol,
    "/root/.cache/vllm": vllm_cache_vol,
}

# Import requests inside image context for use in enter() methods
with vllm_image.imports():
    import requests as _requests


def _wait_ready(proc: subprocess.Popen):
    """Busy-poll until vLLM server is accepting connections."""
    while True:
        try:
            socket.create_connection(("localhost", VLLM_PORT), timeout=1).close()
            return
        except OSError:
            if proc.poll() is not None:
                raise RuntimeError(f"vLLM exited with code {proc.returncode}")


def _warmup(model_name: str):
    """Run a few requests to capture JIT/CUDA artifacts before snapshot."""
    payload = {"model": model_name, "prompt": "Hello", "max_tokens": 8}
    for _ in range(3):
        _requests.post(
            f"http://localhost:{VLLM_PORT}/v1/completions",
            json=payload, timeout=300,
        ).raise_for_status()


def _sleep():
    _requests.post(f"http://localhost:{VLLM_PORT}/sleep?level=1").raise_for_status()


def _wake_up():
    _requests.post(f"http://localhost:{VLLM_PORT}/wake_up").raise_for_status()


def _make_gpu_cls(gpu: str):
    """Factory: creates a Modal class for a specific GPU tier with full vLLM streaming."""

    class ModalClass:
        model_name: str = modal.parameter()

        @modal.enter(snap=True)
        def start(self):
            """Start vLLM subprocess, warmup, then sleep for snapshot."""
            from huggingface_hub import snapshot_download
            import pynvml

            # Pre-download model weights
            snapshot_download(self.model_name)

            # Capture GPU info
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            self._gpu_name = pynvml.nvmlDeviceGetName(handle)
            self._gpu_memory_total_mb = round(
                pynvml.nvmlDeviceGetMemoryInfo(handle).total / 1024 / 1024
            )
            pynvml.nvmlShutdown()

            cmd = [
                "vllm", "serve", self.model_name,
                "--host", "0.0.0.0",
                "--port", str(VLLM_PORT),
                "--gpu-memory-utilization", "0.9",
                "--max-model-len", "4096",
                "--trust-remote-code",
                "--enable-sleep-mode",
                "--max-num-seqs", "4",
            ]

            print(f"Starting vLLM: {' '.join(cmd)}")
            self.vllm_proc = subprocess.Popen(cmd)
            _wait_ready(self.vllm_proc)
            _warmup(self.model_name)
            _sleep()  # offload weights to CPU for snapshot
            print("vLLM sleeping, ready for snapshot")

        @modal.enter(snap=False)
        def restore(self):
            """After snapshot restore: wake up vLLM to reload weights to GPU."""
            _wake_up()
            _wait_ready(self.vllm_proc)
            print("vLLM restored from snapshot")

        @modal.method()
        async def generate_stream(
            self, prompt: str, max_tokens: int = 2048, temperature: float = 0.7
        ):
            """
            Async generator yielding structured chunks (same interface as before):
              1. {"stage": "generating"}                    — model loaded, starting inference
              2. {"stage": "token", "delta": ...}           — each new token
              3. {"stage": "metrics_update", "metrics": {}} — periodic running metrics
              4. {"stage": "complete", "metrics": {}}       — final metrics + GPU stats
            """
            import aiohttp
            import json
            import pynvml

            yield {"stage": "generating"}

            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)

            start = time.perf_counter()
            ttft = None
            full_text = ""
            token_count = 0
            prompt_tokens = 0
            finish_reason = "unknown"
            last_metrics_time = start

            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": True,
                "stream_options": {"include_usage": True},
            }

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"http://localhost:{VLLM_PORT}/v1/completions",
                        json=payload,
                    ) as resp:
                        async for raw in resp.content:
                            line = raw.decode().strip()
                            if not line or line == "data: [DONE]":
                                continue
                            if line.startswith("data: "):
                                line = line[len("data: "):]

                            try:
                                chunk = json.loads(line)
                            except json.JSONDecodeError:
                                continue

                            # Usage-only final chunk
                            if "usage" in chunk and chunk.get("choices", [{}])[0].get("text", "") == "":
                                usage = chunk["usage"]
                                prompt_tokens = usage.get("prompt_tokens", prompt_tokens)
                                token_count = usage.get("completion_tokens", token_count)
                                continue

                            choice = chunk.get("choices", [{}])[0]
                            delta = choice.get("text", "")

                            if delta:
                                if ttft is None:
                                    ttft = time.perf_counter() - start
                                full_text += delta
                                token_count += 1
                                yield {"stage": "token", "delta": delta}

                            if choice.get("finish_reason"):
                                finish_reason = choice["finish_reason"]

                            # Periodic metrics (~every 500ms)
                            now = time.perf_counter()
                            if ttft is not None and now - last_metrics_time >= METRICS_INTERVAL:
                                elapsed = now - start
                                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                                mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
                                yield {
                                    "stage": "metrics_update",
                                    "metrics": {
                                        "ttft_ms": round(ttft * 1000, 2),
                                        "tpot_ms": round(
                                            ((elapsed - ttft) / max(token_count - 1, 1)) * 1000, 2
                                        ),
                                        "tokens_per_second": round(token_count / elapsed, 2),
                                        "e2e_latency_ms": round(elapsed * 1000, 2),
                                        "gpu_utilization_pct": util.gpu,
                                        "gpu_memory_used_mb": round(mem.used / 1024 / 1024),
                                        "completion_tokens": token_count,
                                    },
                                }
                                last_metrics_time = now

                # Final metrics
                end = time.perf_counter()
                e2e_ms = (end - start) * 1000
                ttft_ms = (ttft or 0) * 1000
                tpot_ms = (
                    (e2e_ms - ttft_ms) / (token_count - 1)
                    if token_count > 1
                    else 0
                )

                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)

                yield {
                    "stage": "complete",
                    "metrics": {
                        "response_text": full_text,
                        "finish_reason": finish_reason,
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": token_count,
                        "total_tokens": prompt_tokens + token_count,
                        "ttft_ms": round(ttft_ms, 2),
                        "tpot_ms": round(tpot_ms, 2),
                        "tokens_per_second": (
                            round(token_count / (e2e_ms / 1000), 2)
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

        @modal.exit()
        def stop(self):
            self.vllm_proc.terminate()

    ModalClass.__name__ = f"Model{gpu}"
    ModalClass.__qualname__ = f"Model{gpu}"

    return app.cls(
        gpu=gpu,
        image=vllm_image,
        enable_memory_snapshot=True,
        experimental_options={"enable_gpu_snapshot": True},
        scaledown_window=300,
        volumes=VOLUMES,
        secrets=[modal.Secret.from_name("huggingface")],
        timeout=10 * 60,
    )(ModalClass)


ModelT4 = _make_gpu_cls("T4")
ModelA10G = _make_gpu_cls("A10G")
ModelA100 = _make_gpu_cls("A100")
ModelH100 = _make_gpu_cls("H100")
