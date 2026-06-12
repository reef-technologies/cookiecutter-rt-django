provider "aws" {
  region = var.region
}

resource "aws_ecr_repository" "app" {
  name                 = "${var.name}-prod"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "app_staging" {
  name                 = "${var.name}-staging"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "backups" {
  name                 = "${var.name}-prod-backups"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "backups_staging" {
  name                 = "${var.name}-staging-backups"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}