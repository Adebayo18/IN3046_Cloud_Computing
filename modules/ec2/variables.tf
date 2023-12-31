variable "instance_type" {
  description = "EC2 Instance type"
}

variable "ui_container_port" {
  description = "UI Container port used"
}

variable "key_name" {
  description = "EC2 Key Pair name"
}

variable "ec2_profile_name" {
  description = "EC2 Instance Profile Name"
  default = "ec2-profile"
}

variable "ec2_tag" {
  description = "EC2 name tag"
}

variable "security_group_name" {
  type = string
}

variable "iam_role_name" {
  description = "The name of the IAM role for the EC2 instance"
  type        = string
}

