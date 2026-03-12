#!/bin/bash
set -euo pipefail

AWS_REGION=${AWS_REGION:-us-east-1}
IMAGE_TAG=${1:-latest}
SECRET_ID=${SECRET_ID:-neuralripper-prod}

# ---- Install dependencies ----

sudo apt-get update
sudo apt-get install -y jq unzip gzip curl

# Install AWS CLI v2
if ! command -v aws &> /dev/null; then
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -qo /tmp/awscliv2.zip -d /tmp
  sudo /tmp/aws/install
  rm -rf /tmp/awscliv2.zip /tmp/aws
fi

# Ensure current user can run docker without sudo
sudo usermod -aG docker "$USER"

# ---- Build & push images to ECR ----

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin "$ECR_URL"

docker build -t "$ECR_URL/neuralripper-backend:$IMAGE_TAG" -f backend/Dockerfile backend/
docker build \
  --build-arg VITE_API_BASE_URL=https://neuralripper.com/api \
  --build-arg VITE_WS_BASE_URL=wss://neuralripper.com \
  --build-arg VITE_GOOGLE_CLIENT_ID=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_ID" --region "$AWS_REGION" \
    --query SecretString --output text | jq -r '.GOOGLE_CLIENT_ID') \
  -t "$ECR_URL/neuralripper-frontend:$IMAGE_TAG" \
  -f Dockerfile.frontend .

docker push "$ECR_URL/neuralripper-backend:$IMAGE_TAG"
docker push "$ECR_URL/neuralripper-frontend:$IMAGE_TAG"

# ---- Fetch secrets & deploy ----

SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_ID" --region "$AWS_REGION" \
  --query SecretString --output text)

export AWS_ACCOUNT_ID AWS_REGION IMAGE_TAG
export MYSQL_ROOT_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.MYSQL_ROOT_PASSWORD')
export MYSQL_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.MYSQL_PASSWORD')
export JWT_SECRET_KEY=$(echo "$SECRET_JSON" | jq -r '.JWT_SECRET_KEY')
export GOOGLE_CLIENT_ID=$(echo "$SECRET_JSON" | jq -r '.GOOGLE_CLIENT_ID')
export MODAL_TOKEN_ID=$(echo "$SECRET_JSON" | jq -r '.MODAL_TOKEN_ID')
export MODAL_TOKEN_SECRET=$(echo "$SECRET_JSON" | jq -r '.MODAL_TOKEN_SECRET')

docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans

echo "Deployed with IMAGE_TAG=$IMAGE_TAG"
