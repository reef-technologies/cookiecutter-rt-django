terraform {
  backend "s3" {
    bucket = "{{ cookiecutter.aws_infra_bucket }}"
    key    = "staging/main.tfstate"
    region = "{{ cookiecutter.aws_region }}"
  }
}
