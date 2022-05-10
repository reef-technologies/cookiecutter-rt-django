terraform {
  backend "s3" {
    bucket = "{{ cookiecutter.aws_infra_bucket }}"
    key    = "core.tfstate"
    region = "{{ cookiecutter.aws_region }}"
  }

  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "~> 3.0"
    }
  }

  required_version = "~> 1.0"
}