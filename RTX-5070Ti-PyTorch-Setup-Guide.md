# RTX 5070 Ti (sm_120) PyTorch Training Setup - Solution Guide

## Final Working Solution

### Dockerfile (`docker/Dockerfile.train`)

```dockerfile
FROM nvcr.io/nvidia/pytorch:25.02-py3

# Set working directory
WORKDIR /workspace/NeuralRipper

# Copy backend dependency files to extract package list
COPY backend/pyproject.toml backend/

# Extract and install dependencies directly into container's Python (skip torch/torchvision as they're already in NVIDIA image)
# Pin numpy<2 for PyTorch compatibility
RUN pip install --no-cache-dir \
    "numpy<2" \
    mlflow boto3 datasets transformers ultralytics \
    opencv-python scikit-learn matplotlib pandas \
    ipykernel jupyterlab awscli fastapi uvicorn \
    jupyter-client nbformat ipython ipywidgets

# Register container's Python as Jupyter kernel
RUN python -m ipykernel install --user --name=neuralripper --display-name="NeuralRipper (GPU)"

# Set working directory to notebooks for Jupyter
WORKDIR /workspace/NeuralRipper/notebooks

# Expose Jupyter port
EXPOSE 8888

# Start Jupyter Lab without authentication (localhost access only)
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser", "--notebook-dir=/workspace/NeuralRipper/notebooks", "--ServerApp.token=", "--ServerApp.password="]
```

### Docker Commands

**Build the image:**
```bash
cd /home/dizzydoze/Workspaces/NeuralRipper
docker build -f docker/Dockerfile.train -t neuralripper-training .
```

**Run the container:**
```bash
docker run --gpus all -d \
  --name neuralripper-jupyter \
  -v /home/dizzydoze/Workspaces/NeuralRipper:/workspace/NeuralRipper \
  -v /home/dizzydoze/.aws:/root/.aws:ro \
  -p 127.0.0.1:8888:8888 \
  --restart unless-stopped \
  neuralripper-training
```

**Access Jupyter:**
```
http://localhost:8888
```

---

## Problem Breakdown & Solution Components

### Problem 1: RTX 5070 Ti Compute Capability sm_120 Not Supported

**Issue:**
- RTX 5070 Ti has compute capability **sm_120** (Blackwell architecture)
- Standard PyTorch 2.7.1 only supports up to **sm_90**
- Error: `CUDA error: no kernel image is available for execution on the device`

**Solution:**
```dockerfile
FROM nvcr.io/nvidia/pytorch:25.02-py3
```

**Why it works:**
- NVIDIA's official PyTorch container (25.02) is compiled with sm_120 support
- Uses PyTorch 2.7.0a0 with CUDA 12.8
- Pre-compiled kernels for Blackwell architecture
- No need to build PyTorch from source

---

### Problem 2: Virtual Environment Overriding Container's PyTorch

**Issue:**
- Using `uv sync` creates a virtual environment with PyTorch 2.7.1 (no sm_120 support)
- Mounted volume includes `backend/.venv/` from host
- Jupyter kernel uses the wrong PyTorch: `/workspace/NeuralRipper/backend/.venv/lib/python3.11/site-packages/torch/`
- Container's compatible PyTorch gets ignored

**Solution:**
```dockerfile
# Use pip directly into container's system Python (NO uv)
RUN pip install --no-cache-dir \
    mlflow boto3 datasets transformers ultralytics \
    opencv-python scikit-learn matplotlib pandas \
    ipykernel jupyterlab awscli fastapi uvicorn \
    jupyter-client nbformat ipython ipywidgets
```

**Why it works:**
- Installs dependencies into container's system Python
- Preserves NVIDIA's pre-compiled PyTorch with sm_120 support
- No virtual environment to override the correct PyTorch
- Direct access to `/usr/local/lib/python3.12/dist-packages/torch/`

---

### Problem 3: NumPy 2.x Incompatibility

**Issue:**
- NVIDIA PyTorch container compiled against NumPy 1.x
- Installing dependencies pulls NumPy 2.2.6 by default
- Error: `A module that was compiled using NumPy 1.x cannot be run in NumPy 2.2.6 as it may crash`
- PyTorch fails to initialize NumPy integration

**Solution:**
```dockerfile
RUN pip install --no-cache-dir \
    "numpy<2" \
    mlflow boto3 datasets ...
```

**Why it works:**
- Pins NumPy to 1.x versions (compatible with container's PyTorch)
- Prevents dependency resolver from upgrading to NumPy 2.x
- Must be specified **first** in the pip install command

---

### Problem 4: PyArrow Version Conflict

**Issue:**
- Container includes `cudf` and `pylibcudf` requiring `pyarrow<19.0.0`
- Our dependencies (datasets, transformers) pulled `pyarrow 21.0.0`
- Warning: `cudf 24.12.0 requires pyarrow<19.0.0a0,>=14.0.0`

**Status:**
- Non-blocking warning (doesn't break training)
- Only affects RAPIDS/cudf functionality (not used in our training)
- Can be safely ignored unless using RAPIDS libraries

---

### Problem 5: AWS Credentials for MLflow

**Issue:**
- `training_lib` uses AWS Secrets Manager to fetch MLflow credentials
- Error: `Failed to load secret neuralripper: Unable to locate credentials`
- Container has no access to host's AWS credentials

**Solution:**
```bash
-v /home/dizzydoze/.aws:/root/.aws:ro
```

**Why it works:**
- Mounts host's `~/.aws/` directory into container
- Read-only (`:ro`) for security
- More secure than passing env vars
- No credentials exposed in `docker inspect`

**Alternative (Environment Variables):**
```bash
-e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
-e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
-e AWS_DEFAULT_REGION=us-east-1
```

---

### Problem 6: Jupyter Authentication

**Issue:**
- Default Jupyter requires token/password authentication
- Token changes on every container restart
- HTTP 403 Forbidden errors when accessing without token

**Solution:**
```dockerfile
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--allow-root", "--no-browser", "--notebook-dir=/workspace/NeuralRipper/notebooks", "--ServerApp.token=", "--ServerApp.password="]
```

**Security consideration:**
```bash
-p 127.0.0.1:8888:8888
```

**Why it works:**
- `--ServerApp.token=` and `--ServerApp.password=` disable authentication
- Port bound to `127.0.0.1` (localhost only) - not exposed to network
- Safe for single-user local development
- No need to copy tokens from logs

---

### Problem 7: Jupyter Kernel Registration

**Issue:**
- Container's Python needs to be available as a Jupyter kernel
- Default kernel might use wrong Python interpreter

**Solution:**
```dockerfile
RUN python -m ipykernel install --user --name=neuralripper --display-name="NeuralRipper (GPU)"
```

**Why it works:**
- Registers container's Python as a named kernel
- Easy to identify in Jupyter's kernel selector
- Uses correct Python with NVIDIA PyTorch

---

### Problem 8: Container Persistence

**Issue:**
- Need Jupyter to stay running across system reboots
- Want to avoid rebuilding/restarting container repeatedly

**Solution:**
```bash
--restart unless-stopped \
-d \
--name neuralripper-jupyter
```

**Why it works:**
- `-d`: Runs in background (detached mode)
- `--restart unless-stopped`: Auto-restart on system reboot
- `--name`: Named container for easy management
- `--rm` NOT used: Container persists between stops/starts

---

## Container Management

```bash
# Stop Jupyter
docker stop neuralripper-jupyter

# Start Jupyter
docker start neuralripper-jupyter

# View logs
docker logs -f neuralripper-jupyter

# Rebuild (when updating dependencies)
docker build -f docker/Dockerfile.train -t neuralripper-training .
docker rm -f neuralripper-jupyter
# Then run the full docker run command again
```

---

## Verification Commands

**Check PyTorch version and GPU support:**
```bash
docker exec neuralripper-jupyter python -c "import torch; print('PyTorch:', torch.__version__); print('CUDA:', torch.version.cuda); print('GPU:', torch.cuda.get_device_name(0))"
```

**Test CUDA functionality:**
```bash
docker exec neuralripper-jupyter python -c "import torch; x = torch.randn(2, 2).cuda(); print('CUDA works:', x.device)"
```

---

## Key Takeaways

1. **Use NVIDIA's official containers** for cutting-edge GPU support - they're compiled with latest CUDA architectures
2. **Avoid virtual environments in containers** when the base image already has critical dependencies (like PyTorch)
3. **Pin NumPy < 2** when using PyTorch compiled against NumPy 1.x
4. **Mount AWS credentials** instead of passing as env vars for better security
5. **Bind to localhost** (`127.0.0.1`) when disabling Jupyter authentication
6. **Register kernels explicitly** to ensure Jupyter uses the correct Python interpreter
7. **Use persistent containers** with `--restart unless-stopped` for production-like setup

---

## Architecture Comparison

### ❌ Original (Broken)
```
Jupyter → uv venv Python 3.11 → PyTorch 2.7.1 (sm_90) → ❌ RTX 5070 Ti (sm_120)
                                   ↑
                        Mounted from host (.venv/)
```

### ✅ Final (Working)
```
Jupyter → Container Python 3.12 → NVIDIA PyTorch 2.7.0a0 (sm_120) → ✅ RTX 5070 Ti (sm_120)
                                          ↑
                                NVIDIA official build
```

---

## Batch Size Calculation for GPU Training

### Basic Equation

```
Max_Batch_Size = (Available_VRAM - Model_Memory) / Memory_Per_Sample
```

**Where:**
- `Available_VRAM` = Total GPU memory × 0.85 (leave 15% buffer)
- `Model_Memory` = Model parameters + gradients + optimizer states
- `Memory_Per_Sample` = Activation memory per single sample

### Practical Calculation

**For 16 GB VRAM:**

```
Available_VRAM = 16 GB × 0.85 = 13.6 GB

Current_Batch_Size = 256
Current_Memory_Used = 10.35 GB

Memory_Per_Sample = 10.35 GB / 256 = 0.0404 GB/sample

Max_Batch_Size = 13.6 GB / 0.0404 GB/sample ≈ 336
```

**Safe recommendation: Use batch size = 320** (rounded down for safety)

### Quick Scaling Formula

```
New_Batch_Size = Current_Batch_Size × (Available_Memory / Current_Memory)

New_Batch_Size = 256 × (13.6 / 10.35) ≈ 336
```

### Rule of Thumb

**Start with:** `Batch_Size = 32 × (VRAM_GB / 8)`

For 16 GB VRAM:
- Conservative: `32 × (16 / 8) = 64`
- Moderate: `64 × (16 / 8) = 128`
- Aggressive: `128 × (16 / 8) = 256`

**Note:** Your system RAM (64 GB) only matters for CPU operations like data loading - doesn't affect GPU batch size.
