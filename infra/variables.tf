variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
  default     = "970547374353"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "AWS key pair name"
  type        = string
  default     = "neuralripper-app-key"
}

variable "private_key_path" {
  description = "Local path to SSH private key (for remote-exec provisioner)"
  type        = string
  default     = "~/.ssh/neuralripper-app-key.pem"
}

variable "vpc_id" {
  description = "Existing VPC ID"
  type        = string
  default     = "vpc-0ba2af191bafafa80"
}

variable "subnet_id" {
  description = "Existing public subnet ID"
  type        = string
  default     = "subnet-088fbee10dae55b55"
}

variable "security_group_id" {
  description = "Existing security group ID"
  type        = string
  default     = "sg-0a96d92f689053b0e"
}

variable "eip_allocation_id" {
  description = "Existing Elastic IP allocation ID"
  type        = string
  default     = "eipalloc-0e570c3621550f261"
}

variable "instance_profile_name" {
  description = "Existing IAM instance profile name"
  type        = string
  default     = "neuralripper-ec2-role"
}

variable "secret_id" {
  description = "AWS Secrets Manager secret ID"
  type        = string
  default     = "neuralripper-prod"
}

variable "domain_name" {
  description = "Domain name for TLS certificate"
  type        = string
  default     = "neuralripper.com"
}

variable "image_tag" {
  description = "Docker image tag — change this to trigger redeployment"
  type        = string
  default     = "latest"
}
