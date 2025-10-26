"""
NeuralRipper Modal Inference - Serverless GPU for Multi-Model Streaming

Deployment: modal deploy modal_serve.py
"""

import modal
import os

app = modal.App(name="neuralripper-inference")
volume = modal.Volume.from_name("neuralripper-models", create_if_missing=True)

image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install("vllm", "mlflow", "boto3", "transformers", "huggingface_hub")
)

@app.function(
    image=image,
    volumes={"/models": volume},
    secrets=[modal.Secret.from_name("mlflow"), modal.Secret.from_name("aws")],
    timeout=3600,
)
def download_model_from_mlflow(model_name: str, run_id: str):
    """Download model from MLflow S3 to Modal Volume."""
    import boto3
    from mlflow.tracking import MlflowClient

    print(f"Downloading {model_name} from MLflow run {run_id}...")

    # Connect to MLflow
    mlflow_username = os.environ["MLFLOW_SERVER_USERNAME"]
    mlflow_password = os.environ["MLFLOW_SERVER_PASSWORD"]
    tracking_url = f"https://{mlflow_username}:{mlflow_password}@neuralripper.com/mlflow"
    mlflow_client = MlflowClient(tracking_uri=tracking_url)

    # Get S3 path
    run = mlflow_client.get_run(run_id=run_id)
    artifact_uri = run.info.artifact_uri

    if not artifact_uri.startswith("s3://"):
        raise ValueError(f"Expected S3 URI, got: {artifact_uri}")

    s3_path = artifact_uri[5:]
    bucket = s3_path.split('/')[0]
    prefix = '/'.join(s3_path.split('/')[1:])
    if not prefix.endswith('/'):
        prefix += '/'

    print(f"S3: s3://{bucket}/{prefix}")

    # Download from S3
    s3_client = boto3.client('s3')
    local_path = f"/models/{model_name}"
    os.makedirs(local_path, exist_ok=True)

    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if 'Contents' not in page:
            continue

        for obj in page['Contents']:
            s3_key = obj['Key']
            relative_path = s3_key[len(prefix):]
            if not relative_path:
                continue

            local_file = os.path.join(local_path, relative_path)
            os.makedirs(os.path.dirname(local_file), exist_ok=True)
            print(f"  {s3_key} -> {local_file}")
            s3_client.download_file(bucket, s3_key, local_file)

    volume.commit()
    print(f"✓ Model {model_name} cached in Volume")


@app.function(
    image=image,
    volumes={"/models": volume},
    timeout=3600,
)
def download_model_from_huggingface(model_name: str, hf_model_id: str):
    """Download model from HuggingFace to Modal Volume."""
    from huggingface_hub import snapshot_download

    print(f"Downloading {hf_model_id} as {model_name}...")

    snapshot_download(
        repo_id=hf_model_id,
        local_dir=f"/models/{model_name}",
        local_dir_use_symlinks=False,
    )

    volume.commit()
    print(f"✓ Model {model_name} cached in Volume")

@app.cls(
    gpu="A100",
    image=image,
    volumes={"/models": volume},
    scaledown_window=300,  # Keep warm 5 min
)
@modal.concurrent(max_inputs=10)  # Handle 10 concurrent requests
class Model:
    """
    vLLM inference with real token streaming.
    GPU memory snapshot enables 5-10s cold start after first load.
    """

    model_name: str = modal.parameter()

    @modal.enter()
    async def load_model(self):
        """Load model once when container starts."""
        from vllm.engine.arg_utils import AsyncEngineArgs
        from vllm.engine.async_llm_engine import AsyncLLMEngine

        print(f"Loading {self.model_name} from /models/{self.model_name}/...")

        engine_args = AsyncEngineArgs(
            model=f"/models/{self.model_name}",
            gpu_memory_utilization=0.9,
            max_model_len=4096,
            trust_remote_code=True,
        )
        self.engine = AsyncLLMEngine.from_engine_args(engine_args)

        print(f"✓ Model {self.model_name} ready")

    @modal.method()
    async def generate_stream(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 500
    ):
        """
        Stream tokens as they're generated (real streaming).

        Args:
            messages: [{"role": "user", "content": "..."}]
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Yields:
            str: Individual tokens
        """
        from vllm import SamplingParams
        import uuid

        # Convert to prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

        sampling_params = SamplingParams(
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=0.95,
        )

        # Real streaming
        request_id = str(uuid.uuid4())
        results = self.engine.generate(prompt, sampling_params, request_id)

        previous_text = ""
        async for output in results:
            current_text = output.outputs[0].text
            new_text = current_text[len(previous_text):]
            if new_text:
                yield new_text
            previous_text = current_text


# ==============================================================================
# Testing CLI
# ==============================================================================

@app.local_entrypoint()
def main(
    action: str = "help",
    model_name: str = "qwen",
    run_id: str = "",
    hf_model_id: str = "",
):
    """
    Test deployment locally.

    Examples:
        modal run modal_serve.py --action download-hf --model-name qwen --hf-model-id Qwen/Qwen2.5-0.5B-Instruct
        modal run modal_serve.py --action stream --model-name qwen
    """

    if action == "download-hf":
        if not hf_model_id:
            print("ERROR: --hf-model-id required")
            return
        download_model_from_huggingface.remote(model_name, hf_model_id)

    elif action == "download-mlflow":
        if not run_id:
            print("ERROR: --run-id required")
            return
        download_model_from_mlflow.remote(model_name, run_id)

    elif action == "stream":
        print(f"Testing streaming with {model_name}...")
        test_messages = [{"role": "user", "content": "Tell me a short story."}]

        model = Model(model_name=model_name)
        print("Response: ", end="", flush=True)

        for chunk in model.generate_stream.remote_gen(
            messages=test_messages,
            temperature=0.8,
            max_tokens=150
        ):
            print(chunk, end="", flush=True)

        print("\nDone")

    else:
        print("""
            Usage:
            Download from HuggingFace:
                modal run modal_serve.py --action download-hf \\
                --model-name qwen \\
                --hf-model-id Qwen/Qwen2.5-0.5B-Instruct

            Download from MLflow:
                modal run modal_serve.py --action download-mlflow \\
                --model-name custom-model \\
                --run-id <mlflow-run-id>

            Test streaming:
                modal run modal_serve.py --action stream --model-name qwen

            Deploy to Modal:
                modal deploy modal_serve.py
            """
        )
