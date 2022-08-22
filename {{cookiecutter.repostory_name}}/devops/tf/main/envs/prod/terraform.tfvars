# each of this vars can be overriden by adding ENVIRONMENT variable with name:
# TF_VAR_var_name="value"

name             = "{{ cookiecutter.aws_project_name }}"
region           = "{{ cookiecutter.aws_region }}"
env              = "prod"

# VPC and subnet CIDR settings, change them if you need to pair
# multiple CIDRs (i.e. with different component)
vpc_cidr         = "10.2.0.0/16"
subnet_cidrs     = ["10.2.1.0/24", "10.2.2.0/24"]
azs              = ["{{ cookiecutter.aws_region}}c", "{{ cookiecutter.aws_region}}d"]

# By default, we have an ubuntu image
base_ami_image        = "{{ cookiecutter.aws_ami_image}}"
base_ami_image_owner  = "{{ cookiecutter.aws_ami_image_owner }}"

# domain setting
base_domain_name = "{{ cookiecutter.aws_base_domain_name }}"
domain_name      = "{{ cookiecutter.aws_domain_name }}"

# default ssh key
ec2_ssh_key      = "{{ cookiecutter.aws_ec2_ssh_key }}"

instance_type     = "t3.medium"
rds_instance_type = "db.t3.small"

# defines if we use EC2-only healthcheck or ELB healthcheck
# EC2 healthcheck reacts only on internal EC2 checks (i.e. if machine cannot be reached)
# recommended for staging = EC2, for prod = ELB
autoscaling_health_check_type = "ELB"