# NeuralRipper

**Production-ready LLM evaluation platform with Modal GPU integration, async request batching, and real-time WebSocket streaming.**

Built for scalable model inference using vLLM on serverless GPU infrastructure.

---

## High-Priority TODOs

### 1. Rate Limiting & IP-Based Frequency Control
- Implement FastAPI middleware to extract real client IP (handle proxy headers)
- Add Redis-backed rate limiter: 20 prompts per hour per IP
- Return 429 status with retry-after header when limit exceeded
- Log rate limit violations for abuse monitoring

### 2. Deep Dive: Inference Flow Architecture
- Create Excalidraw diagram mapping entire inference pipeline:
  - Frontend: WebSocket client → `useEvalWebSocket` hook → message handling
  - Backend: FastAPI WS endpoint → QueueHandler → ModalHandler
  - Modal: Cold start → Model initialization → vLLM engine → Token generation
  - Response path: Token streaming → WebSocket → Frontend state updates
- Build minimal hands-on demo to internalize WebSocket + async patterns
- Document timing breakdown: TTFT, cold start overhead, token latency

### 3. Responsive Terminal UI
- Replace hardcoded ASCII border widths with dynamic calculation
- Use `useRef` + `ResizeObserver` to detect container width changes
- Generate borders programmatically based on available space
- Ensure proper wrapping/truncation for narrow viewports

### 4. Makefile for Docker Workflows
```makefile
app-up:    docker-compose -f docker/docker-compose.dev.yml up -d
app-down:  docker-compose -f docker/docker-compose.dev.yml down
app-build: docker-compose -f docker/docker-compose.dev.yml build
app-logs:  docker-compose -f docker/docker-compose.dev.yml logs -f
app-test:  # Add test commands
```

### 5. MLflow Artifact Storage Cleanup & Optimization
**Current Issues:**
- Artifacts named by cryptic run_id/experiment_id (impossible to identify without querying MLflow)
- Every training run saves its "best checkpoint" → hundreds of redundant artifacts in S3
- No automatic cleanup of obsolete checkpoints when better ones are trained

**Required Changes:**
- Implement **global best-per-model tracking**: Only keep single best checkpoint per model across ALL runs
- Add human-readable naming: `s3://bucket/artifacts/{model_name}/best_checkpoint_v{version}.pth`
- Create cleanup script: Compare new checkpoint metrics against existing best, delete inferior ones
- Add artifact versioning metadata in MLflow tags (loss, accuracy, timestamp)
- Optional: Retention policy for top-N checkpoints per model (e.g., keep best 3)

---

## Features

**Modal Serverless GPU Integration**
- Serverless vLLM inference with automatic scaling
- WebSocket streaming for real-time token generation
- Multi-model support with dynamic loading from volume

**Intelligent Request Batching**
- Async queue-based batching (100ms window, max 5 concurrent)
- Automatic GPU utilization optimization
- Per-model background workers for parallel processing

**MLflow Experiment Tracking**
- Complete training lifecycle management
- S3-backed artifact storage
- HTTP Basic Auth protected interface
- Real-time metrics and model versioning

**Docker-First Architecture**
- Build-time secrets for frontend (AWS SDK during build)
- Runtime secrets for backend (AWS Secrets Manager)
- Multi-platform builds (linux/amd64)
- ECR-ready production images

---

## Architecture

```
User Browser
     │
     ├─ WebSocket Connection (/ws/eval)
     │
     ▼
┌─────────────────────────────────────────────┐
│  Frontend (React + TypeScript)              │
│  - useEvalWebSocket hook                    │
│  - Real-time token streaming                │
│  - Live metrics calculation                 │
└──────────────────┬──────────────────────────┘
                   │ HTTP/WS
                   ▼
┌─────────────────────────────────────────────┐
│  Backend (FastAPI)                          │
│  - WebSocket endpoint (eval_router)         │
│  - QueueHandler (batching + async workers)  │
│  - ModalHandler (GPU inference client)      │
└──────────────────┬──────────────────────────┘
                   │ Modal SDK
                   ▼
┌─────────────────────────────────────────────┐
│  Modal Serverless GPU                       │
│  - vLLM engine (Qwen model)                 │
│  - Auto-scaling containers                  │
│  - Token streaming via remote_gen()         │
└─────────────────────────────────────────────┘
```

**Stack:**
- **Frontend:** React, TypeScript, TailwindCSS, Vite
- **Backend:** FastAPI, Python 3.11, UV package manager
- **GPU Inference:** Modal (serverless), vLLM
- **Infrastructure:** Docker, AWS (Secrets Manager, ECR)
- **Deployment:** Docker Compose (dev), ECR (prod)

---

## Quick Start

### Prerequisites
- Docker & Docker Compose
- AWS Account (for Secrets Manager, ECR)
- Modal Account (for serverless GPU inference)

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/yourusername/neuralripper.git
cd neuralripper

# 2. Set up AWS credentials in environment
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 3. Configure secrets in AWS Secrets Manager (neuralripper secret):
# {
#   "MODAL_TOKEN_ID": "your_modal_token_id",
#   "MODAL_TOKEN_SECRET": "your_modal_token_secret",
#   "GITHUB_API_KEY": "optional",
#   "MLFLOW_TRACKING_USERNAME": "your_username",
#   "MLFLOW_TRACKING_PASSWORD": "your_password",
#   "PRIME_API_KEY": "optional"
# }

# 4. Start all services
docker compose -f docker/docker-compose.dev.yml up -d

# 5. Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# MLflow: http://localhost:5000
```

**Development Workflow:**
```bash
# Rebuild specific service after code changes
docker compose -f docker/docker-compose.dev.yml up -d --build frontend

# View logs
docker compose -f docker/docker-compose.dev.yml logs -f backend

# Stop all services
docker compose -f docker/docker-compose.dev.yml down
```

> **Note:** The architecture has been migrated from RunPod to Modal. Some documentation sections below may reference the old architecture and will be updated soon. For current implementation, see `backend/app/handlers/modal_handler.py` and the architecture diagram above.

---

## Core Components

### 1. Modal Integration (`backend/app/handlers/modal_handler.py`)

Manages vLLM model endpoints on RunPod serverless infrastructure.

**Concept:**
- Maps model names to RunPod endpoint IDs
- Generates OpenAI-compatible URLs (`https://api.runpod.ai/v2/{endpoint_id}/openai/v1`)
- Handles API authentication

**Example:**
```python
# Configure in AWS Secrets Manager or .env
RUNPOD_API_KEY=your_key
RUNPOD_ENDPOINT_QWEN=abc123xyz

# Backend automatically routes requests:
# Model: "qwen/qwen2.5-0.5b-instruct"
# → URL: https://api.runpod.ai/v2/abc123xyz/openai/v1/chat/completions
```

**Customization:**
Add new models in `pod_handler.py`:
```python
model_configs = {
    "qwen/qwen2.5-0.5b-instruct": os.getenv("RUNPOD_ENDPOINT_QWEN"),
    "meta-llama/Llama-3-70b": os.getenv("RUNPOD_ENDPOINT_LLAMA"),  # Add new
}
```

---

### 2. Request Queue & Batching (`backend/app/handlers/queue_handler.py`)

Async batching system for optimized GPU utilization.

**Concept:**
1. Client sends prompt via WebSocket
2. Request added to model-specific queue
3. Background worker collects batch (100ms window, max 5 requests)
4. Concurrent requests sent to vLLM (vLLM batches internally)
5. Tokens streamed back via individual response channels

**Flow:**
```
WebSocket Request
    ↓
Request Queue (per model)
    ↓
Batch Collector (100ms timeout)
    ↓
Concurrent HTTP Requests → vLLM (GPU batching)
    ↓
Token Streaming ← Response Channels
    ↓
WebSocket Response
```

**Customization:**
Adjust batching parameters in `queue_handler.py`:
```python
self.batch_timeout = 0.1    # Max wait: 100ms
self.max_batch_size = 5     # Max concurrent requests
```

**Testing RunPod WebSocket:**
```bash
# Install RunPod SDK
pip install runpod

# Test endpoint (replace with your endpoint ID)
python -c "
import runpod
runpod.api_key = 'your_key'
endpoint = runpod.Endpoint('endpoint_id')

for output in endpoint.run_sync({
    'input': {
        'prompt': 'Explain quantum computing',
        'max_tokens': 100
    }
}):
    print(output, end='', flush=True)
"
```

---

### 3. FastAPI Lifespan Management (`backend/app/main.py`)

Proper async initialization and cleanup of background workers.

**Concept:**
- Startup: Initialize PodHandler, QueueHandler, start background workers
- Runtime: Workers continuously batch and process requests
- Shutdown: Gracefully stop workers (if needed)

**Example:**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    pod_handler = PodHandler()
    queue_handler = QueueHandler(pod_handler)

    pod_handler.init_endpoints()
    queue_handler.start_workers()  # Starts per-model workers

    app.state.queue_handler = queue_handler
    yield  # App runs
    # Shutdown (cleanup if needed)
```

---

### 4. Docker Secret Management

**Build-Time Secrets** (Frontend):
```dockerfile
# Frontend needs secrets during `npm run build`
ARG AWS_ACCESS_KEY_ID
ARG AWS_SECRET_ACCESS_KEY
ENV AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID

# Fetch secrets from AWS Secrets Manager during build
RUN export AWS_SECRET_JSON=$(aws secretsmanager get-secret-value ...) && \
    export VITE_API_BASE_URL=$(echo "$AWS_SECRET_JSON" | jq -r '.API_BASE_URL') && \
    npm run build
```

**Runtime Secrets** (Backend):
```dockerfile
# Backend fetches secrets when container starts
CMD ["/bin/bash", "-c", "\
    export AWS_SECRET_JSON=$(aws secretsmanager get-secret-value ...) && \
    export RUNPOD_API_KEY=$(echo \"$AWS_SECRET_JSON\" | jq -r '.RUNPOD_API_KEY') && \
    uvicorn app.main:app --host 0.0.0.0 --port 8000\
"]
```

**Why?**
- Frontend: Secrets baked into static build (`dist/`) for browser access
- Backend: Secrets fetched at runtime, never in image layers

---

### 5. vLLM OpenAI-Compatible API

**Concept:**
RunPod vLLM endpoints expose OpenAI's `/v1/chat/completions` API.

**Usage:**
```python
# Same code works for OpenAI or RunPod vLLM
async with httpx.AsyncClient() as client:
    async with client.stream(
        "POST",
        f"{base_url}/chat/completions",
        json={
            "model": "qwen/qwen2.5-0.5b-instruct",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True
        },
        headers={"Authorization": f"Bearer {api_key}"}
    ) as response:
        async for line in response.aiter_lines():
            # Process SSE (Server-Sent Events)
            if line.startswith("data: "):
                data = json.loads(line[6:])
                token = data["choices"][0]["delta"]["content"]
                print(token, end="")
```

**Model Validation:**
vLLM validates incoming `model` field matches loaded model name (case-sensitive).

---

### 6. MLflow Experiment Tracking

**Concept:**
- **Metadata:** SQLite in Docker volume (experiments, metrics)
- **Artifacts:** S3 bucket (models, checkpoints)
- **Auth:** HTTP Basic Auth via nginx

**Usage in Training:**
```python
import mlflow

mlflow.set_tracking_uri("https://neuralripper.com/mlflow")
mlflow.set_experiment("my-experiment")

with mlflow.start_run():
    # Log metrics
    mlflow.log_metric("accuracy", 0.95)

    # Log model with signature
    mlflow.pytorch.log_model(
        model,
        "model",
        signature=signature,
        registered_model_name="my-model"
    )
```

**Customization:**
Update S3 bucket in `docker/Dockerfile.mlflow`:
```dockerfile
CMD ["mlflow", "server", \
     "--backend-store-uri", "sqlite:////var/lib/mlflow/mlflow-db/mlflow.db", \
     "--default-artifact-root", "s3://your-bucket/mlflow-artifacts", \
     ...
]
```

---

## Production Build & Deploy

### Build for ECR

```bash
# 1. Set AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret

# 2. Update ECR registry in docker/docker-compose.build.yml
# Replace: 970547374353.dkr.ecr.us-west-2.amazonaws.com
# With: YOUR_ACCOUNT_ID.dkr.ecr.YOUR_REGION.amazonaws.com

# 3. Create ECR repository
aws ecr create-repository --repository-name neuralripper --region us-west-2

# 4. Login to ECR
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

# 5. Build images (linux/amd64 for EC2)
docker compose -f docker/docker-compose.build.yml build

# 6. Push to ECR
docker compose -f docker/docker-compose.build.yml push
```

### Deploy on EC2/ECS

Images are now in ECR. AWS infrastructure (EC2, ECS, etc.) can pull and run them.

**Example docker-compose.yml for production:**
```yaml
services:
  mlflow:
    image: YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:mlflow
    ports: ["5000:5000"]
    restart: unless-stopped
    volumes: [mlflow_data:/var/lib/mlflow/mlflow-db]
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}

  backend:
    image: YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:backend
    ports: ["8000:8000"]
    restart: unless-stopped
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_DEFAULT_REGION=us-west-2

  frontend:
    image: YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:frontend
    ports: ["3000:3000"]
    restart: unless-stopped

  nginx:
    image: YOUR_ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:nginx
    ports: ["80:80", "443:443"]
    restart: unless-stopped
    depends_on: [frontend, backend, mlflow]

volumes:
  mlflow_data:
```

---

## Project Structure

```
NeuralRipper/
├── backend/
│   ├── app/
│   │   ├── handlers/
│   │   │   ├── pod_handler.py       # RunPod endpoint management
│   │   │   └── queue_handler.py     # Async request batching
│   │   ├── routers/
│   │   │   ├── eval_router.py       # WebSocket streaming
│   │   │   ├── experiment_router.py # MLflow experiments
│   │   │   └── run_router.py        # MLflow runs
│   │   └── main.py                  # FastAPI app + lifespan
│   ├── pyproject.toml               # UV dependencies
│   └── uv.lock
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── dashboard/
│   │   │       └── EvalTerminal.tsx # Real-time eval UI
│   │   └── main.tsx
│   └── package.json
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   ├── Dockerfile.mlflow
│   ├── Dockerfile.nginx
│   ├── docker-compose.dev.yml       # Local development
│   └── docker-compose.build.yml     # Production ECR build
├── nginx.conf
└── README.md
```

---

## Configuration

### Environment Variables

**AWS Secrets Manager (Secret ID: `neuralripper`):**
```json
{
  "RUNPOD_API_KEY": "your_runpod_api_key",
  "RUNPOD_ENDPOINT_QWEN": "your_endpoint_id",
  "API_BASE_URL": "https://yourdomain.com/api",
  "GITHUB_API_KEY": "optional_github_token",
  "MLFLOW_TRACKING_USERNAME": "mlflow_user",
  "MLFLOW_TRACKING_PASSWORD": "mlflow_pass",
  "PRIME_API_KEY": "optional_prime_key"
}
```

**Local .env file (for docker-compose):**
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-west-2
```

---

## Troubleshooting

### RunPod Connection Issues

```bash
# Test endpoint directly
curl -X POST https://api.runpod.ai/v2/{endpoint_id}/openai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen/qwen2.5-0.5b-instruct",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

### Model Name Mismatch

```
Error: "model qwen2.5 does not match loaded model qwen/qwen2.5-0.5b-instruct"
```

**Fix:** Use exact model name from RunPod vLLM deployment (case-sensitive).

### Frontend Not Updating After Code Change

```bash
# Rebuild frontend image
docker compose -f docker/docker-compose.dev.yml build --no-cache frontend

# Recreate container from new image
docker compose -f docker/docker-compose.dev.yml up -d --force-recreate frontend

# Hard refresh browser (Cmd+Shift+R on Mac)
```

### MLflow Artifacts Not Saving to S3

```bash
# Verify S3 access from backend container
docker exec -it neuralripper-backend bash
aws s3 ls s3://neuralripper/mlflow-artifacts/

# Check IAM permissions: s3:GetObject, s3:PutObject, s3:ListBucket
```

---

## License

MIT

---

## Acknowledgments

- [vLLM](https://github.com/vllm-project/vllm) - High-throughput LLM serving
- [RunPod](https://www.runpod.io/) - Serverless GPU infrastructure
- [MLflow](https://mlflow.org/) - ML lifecycle management
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
