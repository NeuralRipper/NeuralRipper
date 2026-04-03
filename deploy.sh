#!/bin/bash
# Build, push, and deploy to production.
# Requires: docker, aws cli, terraform
# Requires: .env.deploy in repo root (see .env.prod.example)
set -euo pipefail

ECR_URL="970547374353.dkr.ecr.us-east-1.amazonaws.com"

# 1. ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$ECR_URL"

# 2. Build & push
docker compose --env-file .env.deploy -f docker-compose.prod.yml build backend frontend
docker compose --env-file .env.deploy -f docker-compose.prod.yml push backend frontend

# 3. Deploy (SSH into instance → pull → restart)
cd infra && terraform apply -auto-approve
