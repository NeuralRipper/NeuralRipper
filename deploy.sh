#!/bin/bash
set -euo pipefail

AWS_REGION=${AWS_REGION:-us-east-1}
IMAGE_TAG=${1:-latest}
SECRET_ID=${SECRET_ID:-neuralripper-prod}

# ---- Install dependencies ----

sudo apt-get update
sudo apt-get install -y jq unzip gzip curl

# Install Docker if not present
if ! command -v docker &> /dev/null; then
  sudo apt-get install -y ca-certificates
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc > /dev/null
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker "$USER"
fi

# Use sudo -E for docker if current user isn't in docker group yet
DOCKER="docker"
if ! docker info &> /dev/null; then
  DOCKER="sudo -E docker"
fi

# Install AWS CLI v2
if ! command -v aws &> /dev/null; then
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -qo /tmp/awscliv2.zip -d /tmp
  sudo /tmp/aws/install
  rm -rf /tmp/awscliv2.zip /tmp/aws
fi

# ---- Build & push images to ECR ----

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URL="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

aws ecr get-login-password --region "$AWS_REGION" | \
  $DOCKER login --username AWS --password-stdin "$ECR_URL"

$DOCKER build -t "$ECR_URL/neuralripper-backend:$IMAGE_TAG" -f backend/Dockerfile backend/
$DOCKER build \
  --build-arg VITE_API_BASE_URL=https://neuralripper.com/api \
  --build-arg VITE_WS_BASE_URL=wss://neuralripper.com \
  --build-arg VITE_GOOGLE_CLIENT_ID=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_ID" --region "$AWS_REGION" \
    --query SecretString --output text | jq -r '.GOOGLE_CLIENT_ID') \
  -t "$ECR_URL/neuralripper-frontend:$IMAGE_TAG" \
  -f Dockerfile.frontend .

$DOCKER push "$ECR_URL/neuralripper-backend:$IMAGE_TAG"
$DOCKER push "$ECR_URL/neuralripper-frontend:$IMAGE_TAG"

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
export GITHUB_API_KEY=$(echo "$SECRET_JSON" | jq -r '.GITHUB_API_KEY')

$DOCKER compose -f docker-compose.prod.yml pull
$DOCKER compose -f docker-compose.prod.yml up -d --remove-orphans

echo "Deployed with IMAGE_TAG=$IMAGE_TAG"
