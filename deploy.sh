#!/bin/bash
set -euo pipefail

# ---- Install dependencies ----

if ! command -v docker &> /dev/null; then
  echo "Installing Docker..."
  sudo apt-get update
  sudo apt-get install -y ca-certificates curl
  sudo install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo tee /etc/apt/keyrings/docker.asc > /dev/null
  sudo chmod a+r /etc/apt/keyrings/docker.asc
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
  sudo apt-get update
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  sudo usermod -aG docker "$USER"
  echo "Docker installed. You may need to log out and back in for group changes."
fi

if ! command -v aws &> /dev/null || ! aws --version 2>&1 | grep -q "aws-cli/2"; then
  echo "Installing AWS CLI v2..."
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -qo /tmp/awscliv2.zip -d /tmp
  sudo /tmp/aws/install --update
  rm -rf /tmp/awscliv2.zip /tmp/aws
fi

if ! command -v jq &> /dev/null; then
  echo "Installing jq..."
  sudo apt-get update && sudo apt-get install -y jq
fi

# ---- Deploy ----

AWS_REGION=${AWS_REGION:-us-east-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
IMAGE_TAG=${1:-latest}
SECRET_ID=${SECRET_ID:-neuralripper}

echo "Fetching secrets from AWS Secrets Manager..."
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

echo "Logging in to ECR..."
aws ecr get-login-password --region "$AWS_REGION" | \
  docker login --username AWS --password-stdin \
  "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Deploying with IMAGE_TAG=$IMAGE_TAG..."
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d --remove-orphans

echo "Done."
