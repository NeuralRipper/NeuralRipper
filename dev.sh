#!/bin/bash
# Local dev setup: pull secrets from AWS Secrets Manager, start MySQL in Docker.
# After running this, start backend and frontend manually:
#   cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000
#   cd frontend && npm run dev
set -euo pipefail

AWS_REGION=${AWS_REGION:-us-east-1}
SECRET_ID=${SECRET_ID:-neuralripper-prod}

# ---- Load secrets from AWS Secrets Manager (same as prod) ----

SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_ID" --region "$AWS_REGION" \
  --query SecretString --output text)

export MYSQL_ROOT_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.MYSQL_ROOT_PASSWORD')
export MYSQL_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.MYSQL_PASSWORD')
export JWT_SECRET_KEY=$(echo "$SECRET_JSON" | jq -r '.JWT_SECRET_KEY')
export GOOGLE_CLIENT_ID=$(echo "$SECRET_JSON" | jq -r '.GOOGLE_CLIENT_ID')
export MODAL_TOKEN_ID=$(echo "$SECRET_JSON" | jq -r '.MODAL_TOKEN_ID')
export MODAL_TOKEN_SECRET=$(echo "$SECRET_JSON" | jq -r '.MODAL_TOKEN_SECRET')
export GITHUB_API_KEY=$(echo "$SECRET_JSON" | jq -r '.GITHUB_API_KEY')

# ---- Start MySQL container (skip if already running) ----

if docker ps --format '{{.Names}}' | grep -q '^nr-mysql$'; then
  echo "MySQL container already running"
else
  docker rm -f nr-mysql 2>/dev/null || true
  docker run -d --name nr-mysql \
    -e MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
    -e MYSQL_DATABASE=neuralripper \
    -e MYSQL_USER=neuralripper \
    -e MYSQL_PASSWORD="$MYSQL_PASSWORD" \
    -p 3306:3306 \
    mysql:8.0
  echo "MySQL container started on :3306"
fi

echo "Env vars exported. Start backend and frontend in separate terminals:"
echo "  cd backend && uv run uvicorn main:app --host 0.0.0.0 --port 8000"
echo "  cd frontend && npm run dev"
