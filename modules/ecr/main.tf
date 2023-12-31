resource "aws_ecr_repository" "ui_repo" {
  name = var.ui_repo_name
  image_tag_mutability = "MUTABLE"
  force_delete = true
}

resource "aws_ecr_repository" "handler_repo" {
  name = var.handler_repo_name
  image_tag_mutability = "MUTABLE"
  force_delete = true
}

resource "null_resource" "docker_build_push" {
  for_each = toset(var.ecr_repositories)
  provisioner "local-exec" {
    command = <<EOF
    docker rmi ${each.key} ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${each.key}
    aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com
    docker build -t ${each.key} -f ${each.key}.Dockerfile .
    docker tag ${each.key}:latest ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${each.key}:latest
    docker push ${var.account_id}.dkr.ecr.${var.aws_region}.amazonaws.com/${each.key}:latest
    EOF
  }

  depends_on = [aws_ecr_repository.handler_repo, aws_ecr_repository.ui_repo]
}

data "aws_ecr_repository" "app_images" {
  for_each   = toset(var.ecr_repositories)
  name       = each.key
  depends_on = [null_resource.docker_build_push]
}

locals {
  ui_container_image      = "${data.aws_ecr_repository.app_images[var.ui_repo_name].repository_url}:latest"
  handler_container_image = "${data.aws_ecr_repository.app_images[var.handler_repo_name].repository_url}:latest"
}