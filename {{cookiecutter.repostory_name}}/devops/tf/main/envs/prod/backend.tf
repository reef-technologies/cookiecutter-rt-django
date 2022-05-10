terraform {
  backend "s3" {
    bucket = "{{ cookiecutter.aws_infra_bucket }}"
    key    = "prod/main.tfstate"
    region = "{{ cookiecutter.aws_region }}"
  }
}
