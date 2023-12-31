variable "aws_access_key_id" {
  description = "AWS access key ID"
}

variable "aws_secret_access_key" {
  description = "AWS secret access key"
}

variable "aws_region" {
  description = "AWS region"
}

variable "ui_repo_name" {
  description = "Repo Name for the UI image"
  default = "bugtrackapp"
}

variable "handler_repo_name" {
  description = "Repo Name for the UI image"
  default = "bugtrackhandler"
}

variable "ecr_repositories" {
  description = "Repositories to be created"
  default     = ["bugtrackapp", "bugtrackhandler"]
}

variable "ui_host_port" {
  description = "Port on host to expose for the UI container"
  default     = 5000
}

variable "ui_container_port" {
  description = "UI Container port used"
  default     = 5000
}

variable "handler_host_port" {
  description = "Port on host to expose for the handler container"
  default     = 5001
}

variable "handler_container_port" {
  description = "Handler Container port used"
  default     = 5001
}

variable "instance_type" {
  description = "EC2 Instance Type"
  default     = "t2.micro"
}

variable "key_pair_name" {
  description = "EC2 Key Pair name"
  default     = "Jemzy"
}

variable "env_filename" {
  description = "Environmental variables file name"
  default = "app.env"
}

variable "remote_exec_connection_type" {
  description = "Type of remote connection used by remote-exec provisioner"
  default = "ssh"
}

variable "remote_exec_user" {
  description = "User name for the remote-exec to run commands on the remote host"
  default = "ec2-user"
}
