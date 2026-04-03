terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ──────────────────────────────────────────────
# Data sources — reference existing resources
# ──────────────────────────────────────────────

data "aws_vpc" "main" {
  id = var.vpc_id
}

data "aws_subnet" "public" {
  id = var.subnet_id
}

data "aws_security_group" "main" {
  id = var.security_group_id
}

data "aws_eip" "main" {
  id = var.eip_allocation_id
}

data "aws_iam_instance_profile" "ec2" {
  name = var.instance_profile_name
}

# Latest Ubuntu 24.04 LTS AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# ──────────────────────────────────────────────
# EC2 instance
# ──────────────────────────────────────────────

resource "aws_instance" "app" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  key_name               = var.key_name
  subnet_id              = data.aws_subnet.public.id
  vpc_security_group_ids = [data.aws_security_group.main.id]
  iam_instance_profile   = data.aws_iam_instance_profile.ec2.name

  user_data = join("\n", [
    "#!/bin/bash",
    "cat > /etc/neuralripper.env <<'TFVARS'",
    "AWS_REGION=${var.aws_region}",
    "AWS_ACCOUNT_ID=${var.aws_account_id}",
    "SECRET_ID=${var.secret_id}",
    "DOMAIN=${var.domain_name}",
    "IMAGE_TAG=${var.image_tag}",
    "TFVARS",
    "chmod 600 /etc/neuralripper.env",
    file("${path.module}/user_data.sh"),
  ])

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  tags = {
    Name = "neuralripper-app"
  }

  lifecycle {
    ignore_changes = [ami, user_data]
  }
}

# ──────────────────────────────────────────────
# Elastic IP association
# ──────────────────────────────────────────────

resource "aws_eip_association" "app" {
  instance_id   = aws_instance.app.id
  allocation_id = data.aws_eip.main.id
}

# ──────────────────────────────────────────────
# Redeploy trigger — runs when image_tag changes
# ──────────────────────────────────────────────

resource "null_resource" "redeploy" {
  triggers = {
    always_run = timestamp()
  }

  depends_on = [aws_instance.app, aws_eip_association.app]

  connection {
    type        = "ssh"
    user        = "ubuntu"
    private_key = file(var.private_key_path)
    host        = data.aws_eip.main.public_ip
  }

  provisioner "remote-exec" {
    inline = [
      "echo 'Waiting for cloud-init to finish...'",
      "cloud-init status --wait || true",
      "export AWS_REGION=${var.aws_region}",
      "export AWS_ACCOUNT_ID=${var.aws_account_id}",
      "export IMAGE_TAG=${var.image_tag}",
      "export ECR_URL=${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com",
      "aws ecr get-login-password --region $AWS_REGION | sudo docker login --username AWS --password-stdin $ECR_URL",
      "cd /app && sudo docker compose pull && sudo docker compose up -d --remove-orphans",
      "echo 'Redeployed with IMAGE_TAG=${var.image_tag}'"
    ]
  }
}
