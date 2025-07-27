# NeuralRipper

A comprehensive machine learning platform featuring experiment tracking, real-time dashboards, and model inference capabilities.

## Features

- **Dashboard**: Real-time experiment tracking with live metrics and charts
- **Model Inference**: Text-based model inference with streaming terminal interface
- **Computer Vision Demo**: YOLO detection and Rerun visualizations for images/videos
- **MLflow Integration**: Complete experiment lifecycle management with GCS artifact storage

## Architecture

- **Backend**: FastAPI with MLflow tracking server
- **Frontend**: React with real-time updates and interactive components
- **Storage**: Google Cloud Storage for model artifacts
- **Deployment**: Docker containers on GCP Compute Engine

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-username/neuralripper.git
cd neuralripper

# Local development
cd frontend && pnpm install && pnpm dev
cd backend && pip install -r requirements.txt && uvicorn app.app:app --reload
```

Access at `http://localhost:3000`

## Deployment to GCP

### Prerequisites
- GCP project with billing enabled
- Docker installed locally
- Domain name (optional)

### Build & Push Images

```bash
# Build for AMD64 platform
docker compose -f docker/docker-compose.build.yml build
docker compose -f docker/docker-compose.build.yml push
```

### VM Setup

1. **Create VM Instance**
   ```bash
   # e2-small, Ubuntu 22.04, 30GB disk, us-central1-a
   # Enable HTTP/HTTPS traffic
   # 30GB required for large ML images (6GB+ backend)
   ```

2. **Deploy Application**
   ```bash
   # SSH to VM
   gcloud compute ssh your-vm-name
   
   # Create deployment
   mkdir ml-portfolio && cd ml-portfolio
   gcloud auth configure-docker
   
   # Create docker-compose.yml and nginx.conf (see configs below)
   docker compose pull  # Backend ~6GB due to ML dependencies
   docker compose up -d
   ```

3. **Set Static IP & Domain**
   ```bash
   # Reserve static IP in GCP Console
   # Update DNS A record: yourdomain.com → VM_IP
   # Update nginx.conf server_name to your domain
   docker compose restart nginx
   ```

4. **Enable HTTPS (Optional)**
   ```bash
   # Stop containers first
   docker compose down
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d yourdomain.com
   
   # Update docker-compose.yml to mount SSL certificates
   # Update nginx.conf for HTTPS (see SSL config below)
   docker compose up -d
   ```

### Configuration Files

**docker-compose.yml**
```yaml
services:
  mlflow:
    image: gcr.io/your-project/mlflow-server
    ports: ["5000:5000"]
    restart: unless-stopped
    volumes: [mlflow_data:/data]

  backend:
    image: gcr.io/your-project/backend
    ports: ["8000:8000"]
    restart: unless-stopped
    environment: [MLFLOW_TRACKING_URI=http://mlflow:5000]

  frontend:
    image: gcr.io/your-project/frontend
    ports: ["3000:3000"]
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports: ["80:80"]
    volumes: ["./nginx.conf:/etc/nginx/nginx.conf:ro"]
    restart: unless-stopped
    depends_on: [frontend, backend, mlflow]

volumes:
  mlflow_data:
```

**nginx.conf**
```nginx
events { worker_connections 1024; }
http {
    upstream frontend { server frontend:3000; }
    upstream backend { server backend:8000; }
    upstream mlflow { server mlflow:5000; }

    server {
        listen 80;
        server_name yourdomain.com;  # Update with your domain
        
        location / { proxy_pass http://frontend; }
        location /api/ { proxy_pass http://backend/; }
        location /mlflow/ { proxy_pass http://mlflow/; }
        
        # Standard proxy headers for all locations
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Cost Optimization

- **VM**: e2-small (~$15/month) eliminates cold starts
- **Storage**: 30GB standard disk (~$3/month)
- **Network**: Minimal egress costs for portfolio traffic
- **Total**: ~$20/month for always-on deployment