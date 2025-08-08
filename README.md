# NeuralRipper

A comprehensive machine learning platform featuring experiment tracking, real-time dashboards, and model inference capabilities.

## Features

- **Dashboard**: Real-time experiment tracking with live metrics and charts
- **Model Inference**: Text-based model inference with streaming terminal interface
- **Computer Vision Demo**: YOLO detection and Rerun visualizations for images/videos
- **MLflow Integration**: Complete experiment lifecycle management with S3 artifact storage and HTTP authentication

## Architecture

- **Backend**: FastAPI with MLflow tracking server
- **Frontend**: React with real-time updates and interactive components
- **Storage**: AWS S3 for model artifacts
- **Security**: HTTP Basic Auth for MLflow access
- **Deployment**: Docker containers on AWS Lightsail

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

## Deployment to AWS

### Prerequisites
- AWS account with billing enabled
- Docker installed locally
- Domain name (optional)
- S3 bucket for MLflow artifacts

### Setup AWS CLI

```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip && sudo ./aws/install

# Configure credentials (create IAM user with ECR and S3 permissions)
aws configure
# Enter: Access Key ID, Secret Access Key, us-west-2, json
```

### Environment Configuration

Create environment file with AWS credentials:
```bash
# Copy example and add real values
cp .env.example .env

# Edit .env file with your AWS credentials:
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Build & Push Images

```bash
# Create ECR repository
aws ecr create-repository --repository-name neuralripper

# Login to ECR
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com

# Build for AMD64 platform
docker compose -f docker/docker-compose.build.yml build
docker compose -f docker/docker-compose.build.yml push
```

### Lightsail Setup

1. **Create Lightsail Instance**
   ```bash
   # 2 vCPU, 4GB RAM, 40GB SSD (~$20/month)
   # Ubuntu 22.04, us-west-2
   # Enable HTTP/HTTPS traffic
   ```

2. **Deploy Application**
   ```bash
   # SSH to Lightsail
   ssh -i your-key.pem ubuntu@your-lightsail-ip
   
   # Set up Docker apt respository
     # Add Docker's official GPG key:
     sudo apt-get update
     sudo apt-get install ca-certificates curl
     sudo install -m 0755 -d /etc/apt/keyrings
     sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
     sudo chmod a+r /etc/apt/keyrings/docker.asc

     # Add the repository to Apt sources:
     echo \
     "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
     $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
     sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
     sudo apt-get update

   # Install Docker
   sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y
   sudo usermod -aG docker ubuntu && newgrp docker

   # Start Docker and make it auto launch
   sudo systemctl start docker
   sudo systemctl enable docker
   
   # Install AWS CLI and login
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   aws configure  # Same credentials as local
   
   # ECR login
   aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com
   
   # Create deployment directory
   mkdir neuralripper && cd neuralripper
   
   # Create docker-compose.yml and nginx.conf (see configs below)
   # Set up environment variables
   cp .env.example .env  # Add your AWS credentials
   
   # Deploy application
   docker compose pull
   docker compose up -d
   ```

3. **Domain Setup & SSL Configuration**

   **Step 1: Configure Domain DNS**
   ```bash
   # Get your Lightsail static IP
   # In Lightsail Console: Networking > Create static IP > Attach to instance
   
   # Update your domain provider (GoDaddy, Namecheap, etc.):
   # A Record: @ (or yourdomain.com) → YOUR_LIGHTSAIL_STATIC_IP
   # A Record: www → YOUR_LIGHTSAIL_STATIC_IP
   
   # Verify DNS propagation (may take 5-60 minutes)
   dig yourdomain.com
   nslookup yourdomain.com
   ```

   **Step 2: Install Certbot & Generate SSL Certificates**
   ```bash
   # SSH to your Lightsail instance
   ssh -i your-key.pem ubuntu@your-lightsail-ip
   
   # Stop nginx container temporarily
   docker compose stop nginx
   
   # Install certbot
   sudo apt update
   sudo apt install certbot -y
   
   # Generate SSL certificates (standalone mode)
   sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com
   
   # Certificates will be saved to:
   # /etc/letsencrypt/live/yourdomain.com/fullchain.pem
   # /etc/letsencrypt/live/yourdomain.com/privkey.pem
   ```

   **Step 3: Update Nginx Configuration**
   ```bash
   # Update nginx.conf with your domain name and SSL paths
   # Then restart containers
   docker compose up -d
   
   # Test HTTPS
   curl -I https://yourdomain.com
   ```

   **Step 4: Auto-renewal Setup**
   ```bash
   # Test renewal
   sudo certbot renew --dry-run
   
   # Set up auto-renewal (certificates expire every 90 days)
   sudo crontab -e
   # Add this line:
   # 0 12 * * * /usr/bin/certbot renew --quiet && docker compose restart nginx
   ```

### MLflow Access

MLflow is protected with HTTP Basic Auth:
- **Username**: `dizzydoze`
- **Password**: Set in `Dockerfile.nginx`
- **Access**: `https://yourdomain.com/mlflow/`
- **Purpose**: Secure access for experiment tracking, model management, and artifact storage

### Configuration Files

**.env.example**
```bash
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
```

**docker-compose.yml**
```yaml
services:
  mlflow:
    image: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:mlflow
    ports: ["5000:5000"]
    restart: unless-stopped
    volumes: [mlflow_data:/var/lib/mlflow/mlflow-db]
    environment:
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}

  backend:
    image: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:backend
    restart: unless-stopped
    environment: [MLFLOW_TRACKING_URI=http://mlflow:5000]

  frontend:
    image: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:frontend
    ports: ["3000:3000"]
    restart: unless-stopped

  nginx:
    image: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:nginx
    ports: ["80:80", "443:443"]
    volumes: 
      - "/etc/letsencrypt:/etc/letsencrypt:ro"
    restart: unless-stopped
    depends_on: [frontend, backend, mlflow]

volumes:
  mlflow_data:
```

**docker-compose.build.yml**
```yaml
services:
  mlflow:
    build:
      context: ..
      dockerfile: docker/Dockerfile.mlflow
      platforms: [linux/amd64]
    image: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:mlflow

  backend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.backend
      platforms: [linux/amd64]
    image: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:backend
  
  frontend:
    build:
      context: ..
      dockerfile: docker/Dockerfile.frontend
      platforms: [linux/amd64]
      args:
        AWS_ACCESS_KEY_ID: ${AWS_ACCESS_KEY_ID}
        AWS_SECRET_ACCESS_KEY: ${AWS_SECRET_ACCESS_KEY}
    image: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:frontend

  nginx:
    build:
      context: ..
      dockerfile: docker/Dockerfile.nginx
      platforms: [linux/amd64]
    image: ACCOUNT_ID.dkr.ecr.us-west-2.amazonaws.com/neuralripper:nginx
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
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name yourdomain.com www.yourdomain.com;
        
        ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
        
        location / { 
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /api/ { 
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
        
        location /mlflow/ {
            auth_basic "MLflow Access";
            auth_basic_user_file /etc/nginx/.htpasswd;
            proxy_pass http://mlflow/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
}
```

### Data Storage

MLflow stores two types of data:
- **Metadata** (experiments, runs, metrics): SQLite database in container volume
- **Artifacts** (models, files): AWS S3 bucket

You'll see experiments/runs immediately as metadata is stored in the database. S3 artifacts only appear when you call `mlflow.log_model()` or `mlflow.log_artifact()` in your training code.

### Cost Optimization

- **Lightsail**: 2 vCPU, 4GB RAM (~$20/month)
- **ECR**: ~$1/month for 10GB images
- **S3**: ~$1/month for MLflow artifacts
- **Network**: Minimal data transfer costs
- **Total**: ~$22/month for always-on deployment

Replace `ACCOUNT_ID` with your AWS account ID (get with `aws sts get-caller-identity --query Account --output text`)