# each of this vars can be overriden by adding ENVIRONMENT variable with name:
# TF_VAR_var_name="value"

name             = "{{ cookiecutter.aws_project_name }}"
region           = "{{ cookiecutter.aws_region }}"
env              = "staging"

# VPC and subnet CIDR settings, change them if you need to pair
# multiple CIDRs (i.e. with different component)
vpc_cidr         = "10.20.0.0/16"
subnet_cidrs     = ["10.20.1.0/24", "10.20.2.0/24"]
azs              = ["{{ cookiecutter.aws_region }}a", "{{ cookiecutter.aws_region }}b"]

# By default, we have an ubuntu image
base_ami_image        = "{{ cookiecutter.aws_ami_image }}"
base_ami_image_owner  = "{{ cookiecutter.aws_ami_image_owner }}"

# domain setting
base_domain_name = "{{ cookiecutter.aws_base_domain_name }}"
domain_name      = "{{ cookiecutter.aws_staging_domain_name }}"

# default ssh key
ec2_ssh_key      = "{{ cookiecutter.aws_ec2_ssh_key }}"