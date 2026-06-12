variable "name" {}
variable "env" {}
variable "region" {}

variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnets" {}
variable "azs" {}

variable "base_ami_id" {}
variable "base_domain_name" {}

variable "domain_name" {}
variable "ec2_ssh_key" {}

variable "ecr_base_url" {}
variable "ecr_image" {}
variable "ecr_backups_image" {}

variable "instance_type" {}
variable "health_check_type" {}
variable "account_id" {}
variable "database" {}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed to reach the EC2 instances over SSH (port 22)."
  type        = list(string)
}

variable "monitoring_allowed_cidrs" {
  description = "CIDR blocks allowed to reach the monitoring mTLS endpoint (port 10443)."
  type        = list(string)
}