output "elastic_ip" {
  description = "Public Elastic IP — set this as A record in Namecheap"
  value       = data.aws_eip.main.public_ip
}

output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "instance_type" {
  description = "EC2 instance type"
  value       = aws_instance.app.instance_type
}

output "ami_id" {
  description = "Ubuntu AMI used"
  value       = data.aws_ami.ubuntu.id
}

output "ecr_backend" {
  description = "ECR backend repository URL"
  value       = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/neuralripper-backend"
}

output "ecr_frontend" {
  description = "ECR frontend repository URL"
  value       = "${var.aws_account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/neuralripper-frontend"
}

output "ssh_command" {
  description = "SSH into the instance"
  value       = "ssh -i ${var.private_key_path} ubuntu@${data.aws_eip.main.public_ip}"
}
