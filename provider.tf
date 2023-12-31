terraform {
  required_version = ">= 0.13.1"

  required_providers {
    aws = {
      version = ">= 1.13"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = var.aws_access_key_id
  secret_key = var.aws_secret_access_key
}