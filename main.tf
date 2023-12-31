data "aws_caller_identity" "current" {}

module "ecr" {
  source            = "./modules/ecr"
  ui_repo_name      = var.ui_repo_name
  handler_repo_name = var.handler_repo_name
  ecr_repositories  = var.ecr_repositories
  account_id        = data.aws_caller_identity.current.account_id
  aws_region = var.aws_region
}

module "ec2" {
  source            = "./modules/ec2"
  ec2_tag           = "UI_Instance"
  instance_type     = var.instance_type
  ui_container_port = var.ui_container_port
  depends_on        = [module.ecr]
  key_name          = var.key_pair_name
  security_group_name = "Allow public traffic instance 1"
  iam_role_name     = "ec2_role_instance_1"
  ec2_profile_name = "ec2_profile1"
}

module "ec2_instance_2" {
  source            = "./modules/ec2"
  ec2_tag           = "Handler_Instance"
  instance_type     = var.instance_type
  ui_container_port = var.ui_container_port
  security_group_name = "Allow public traffic instance 2"
  depends_on        = [module.ecr]
  key_name          = var.key_pair_name
  iam_role_name     = "ec2_role_instance_2"
  ec2_profile_name = "ec2_profile2"
}


locals {
  account_id              = data.aws_caller_identity.current.account_id
  ui_container_image      = module.ecr.ui_container_image
  handler_container_image = module.ecr.handler_container_image
}


resource "null_resource" "start_ui_app" {
  connection {
    type        = var.remote_exec_connection_type
    user        = var.remote_exec_user
    host        = module.ec2.dns
    private_key = file("${path.module}/${var.key_pair_name}.pem")
  }

  provisioner "file" {
    source      = "${path.module}/${var.env_filename}"
    destination = "/home/ec2-user/${var.env_filename}"
  }

  provisioner "remote-exec" {
    inline = [
      "set -e",
      "sudo yum update -y",
      "sudo yum install -y git",
      "sudo yum install -y python3-pip",
      "sudo yum install -y docker",
      "sudo service docker start",
      "until sudo systemctl is-active docker; do sleep 10; done",
      "sudo usermod -a -G docker ec2-user",
      "sudo systemctl enable docker",
      "sudo docker version",
      "pwd",
      "aws ecr get-login-password --region ${var.aws_region} | sudo docker login --username AWS --password-stdin ${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com",
      "sudo docker pull ${local.ui_container_image}",
      "sudo docker container run -d --env-file ${var.env_filename} -p ${var.ui_host_port}:${var.ui_container_port} ${local.ui_container_image}",

    ]
  }

  depends_on = [module.ec2]
}


resource "null_resource" "start_handler_app" {
  triggers = {
    always_run = "${timestamp()}"
  }

  connection {
    type        = var.remote_exec_connection_type
    user        = var.remote_exec_user
    host        = module.ec2_instance_2.dns
    private_key = file("${path.module}/${var.key_pair_name}.pem")
  }

  provisioner "file" {
    source      = "${path.module}/${var.env_filename}"
    destination = "/home/ec2-user/${var.env_filename}"
  }

  provisioner "remote-exec" {
    inline = [
      "set -e",
      "set -x",
      "sudo yum update -y",
      "sudo yum install -y git",
      "sudo yum install -y python3-pip",
      "sudo yum install -y docker",
      "sudo service docker start",
      "until sudo systemctl is-active docker; do sleep 10; done",
      "sudo usermod -a -G docker ec2-user",
      "sudo systemctl enable docker",
      "sudo docker version",
      "pwd",
      "aws ecr get-login-password --region ${var.aws_region} | sudo docker login --username AWS --password-stdin ${local.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com",
      "sudo docker pull ${local.handler_container_image}",
      "sudo docker container run -d --env-file ${var.env_filename} -p ${var.handler_host_port}:${var.handler_container_port} ${local.handler_container_image}"

    ]
  }

  depends_on = [module.ec2]
}