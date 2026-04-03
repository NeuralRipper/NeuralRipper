# ── Source config written by Terraform ──
source /etc/neuralripper.env

set -euo pipefail
exec > /var/log/user_data.log 2>&1
echo "=== user_data started at $(date) ==="

ECR_URL="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# ──────────────────────────────────────────────
# 1. Swap (1GB) — essential for t3.micro
# ──────────────────────────────────────────────
if [ ! -f /swapfile ]; then
  fallocate -l 1G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
  sysctl vm.swappiness=10
  echo 'vm.swappiness=10' >> /etc/sysctl.conf
fi

# ──────────────────────────────────────────────
# 2. Install packages
# ──────────────────────────────────────────────
apt-get update
apt-get install -y ca-certificates curl jq unzip certbot

# Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | tee /etc/apt/keyrings/docker.asc > /dev/null
chmod a+r /etc/apt/keyrings/docker.asc
ARCH=$(dpkg --print-architecture)
CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
echo "deb [arch=$ARCH signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $CODENAME stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
usermod -aG docker ubuntu

# AWS CLI v2
if ! command -v aws &> /dev/null; then
  curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o /tmp/awscliv2.zip
  unzip -qo /tmp/awscliv2.zip -d /tmp
  /tmp/aws/install
  rm -rf /tmp/awscliv2.zip /tmp/aws
fi

# ──────────────────────────────────────────────
# 3. Pull Docker images from ECR
# ──────────────────────────────────────────────
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URL"
docker pull "$ECR_URL/neuralripper-backend:$IMAGE_TAG"
docker pull "$ECR_URL/neuralripper-frontend:$IMAGE_TAG"

# ──────────────────────────────────────────────
# 4. Fetch secrets from Secrets Manager
# ──────────────────────────────────────────────
SECRET_JSON=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_ID" --region "$AWS_REGION" \
  --query SecretString --output text)

# ──────────────────────────────────────────────
# 5. Write app files to /app
# ──────────────────────────────────────────────
mkdir -p /app
cd /app

# .env file for docker compose
cat > /app/.env <<ENVEOF
AWS_ACCOUNT_ID=$AWS_ACCOUNT_ID
AWS_REGION=$AWS_REGION
IMAGE_TAG=$IMAGE_TAG
MYSQL_ROOT_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.MYSQL_ROOT_PASSWORD')
MYSQL_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.MYSQL_PASSWORD')
JWT_SECRET_KEY=$(echo "$SECRET_JSON" | jq -r '.JWT_SECRET_KEY')
GOOGLE_CLIENT_ID=$(echo "$SECRET_JSON" | jq -r '.GOOGLE_CLIENT_ID')
MODAL_TOKEN_ID=$(echo "$SECRET_JSON" | jq -r '.MODAL_TOKEN_ID')
MODAL_TOKEN_SECRET=$(echo "$SECRET_JSON" | jq -r '.MODAL_TOKEN_SECRET')
GITHUB_API_KEY=$(echo "$SECRET_JSON" | jq -r '.GITHUB_API_KEY')
ENVEOF
chmod 600 /app/.env

# docker-compose.yml
cat > /app/docker-compose.yml <<'COMPOSEEOF'
services:
  mysql:
    image: mysql:8.0
    env_file: .env
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: neuralripper
      MYSQL_USER: neuralripper
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
      - ./mysql.cnf:/etc/mysql/conf.d/custom.cnf:ro
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      retries: 5
    restart: always
    deploy:
      resources:
        limits:
          memory: 384M

  backend:
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/neuralripper-backend:${IMAGE_TAG:-latest}
    env_file: .env
    environment:
      MYSQL_HOST: mysql
      MYSQL_USER: neuralripper
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      MYSQL_DATABASE: neuralripper
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      MODAL_TOKEN_ID: ${MODAL_TOKEN_ID}
      MODAL_TOKEN_SECRET: ${MODAL_TOKEN_SECRET}
      GITHUB_API_KEY: ${GITHUB_API_KEY}
    depends_on:
      mysql:
        condition: service_healthy
    expose:
      - "8000"
    restart: always
    deploy:
      resources:
        limits:
          memory: 256M

  frontend:
    image: ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/neuralripper-frontend:${IMAGE_TAG:-latest}
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - ./nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
    restart: always
    deploy:
      resources:
        limits:
          memory: 64M

volumes:
  mysql_data:
COMPOSEEOF

# nginx-ssl.conf
cat > /app/nginx-ssl.conf <<NGINXEOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /inference/ws/ {
        proxy_pass http://backend:8000/inference/ws/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_read_timeout 86400;
    }
}
NGINXEOF

# MySQL memory tuning for t3.micro
cat > /app/mysql.cnf <<'MYSQLEOF'
[mysqld]
innodb_buffer_pool_size = 128M
innodb_log_buffer_size  = 8M
max_connections         = 30
key_buffer_size         = 16M
tmp_table_size          = 16M
max_heap_table_size     = 16M
performance_schema      = OFF
MYSQLEOF

# ──────────────────────────────────────────────
# 6. TLS certificate via Certbot
# ──────────────────────────────────────────────
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
  certbot certonly --standalone --non-interactive --agree-tos \
    --email admin@$DOMAIN \
    -d "$DOMAIN"
fi

# Auto-renewal cron
cat > /etc/cron.d/certbot-renew <<'CRONEOF'
0 3,15 * * * root certbot renew --quiet --deploy-hook "docker exec $(docker ps -qf name=frontend) nginx -s reload 2>/dev/null || true"
CRONEOF
chmod 644 /etc/cron.d/certbot-renew

# ──────────────────────────────────────────────
# 7. Start everything
# ──────────────────────────────────────────────
cd /app
docker compose up -d

echo "=== user_data completed at $(date) ==="
