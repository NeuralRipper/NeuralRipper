#!/bin/bash
set -e

echo "=== Installing AWS CLI ==="
curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws

echo "=== Removing old Docker packages ==="
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    sudo apt-get remove -y $pkg 2>/dev/null || true
done

echo "=== Installing Docker ==="
sudo apt-get update
sudo apt-get install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
$(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") stable" | \
sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo "=== Adding user to docker group ==="
sudo usermod -aG docker $USER

echo "=== Setting up AWS credentials ==="
# If ~/.aws/credentials exists, export them
if [ -f ~/.aws/credentials ]; then
    export AWS_ACCESS_KEY_ID=$(aws configure get aws_access_key_id)
    export AWS_SECRET_ACCESS_KEY=$(aws configure get aws_secret_access_key)
    export AWS_DEFAULT_REGION=$(aws configure get region || echo "us-east-1")
fi

echo "=== Logging into ECR ==="
sg docker -c "aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 970547374353.dkr.ecr.us-east-1.amazonaws.com"

echo "=== Cloning repo ==="
if [ ! -d ~/NeuralRipper ]; then
    git clone https://github.com/NeuralRipper/NeuralRipper.git ~/NeuralRipper
fi

echo "=== Starting containers ==="
cd ~/NeuralRipper/docker
sg docker -c "docker compose -f docker-compose.yml pull"
sg docker -c "docker compose -f docker-compose.yml up -d"

echo "=== Done! ==="
echo "You may need to log out and log back in for docker group to take full effect."
echo "Check status: docker ps"
