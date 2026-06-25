variable "region" {
  type = string
}

variable "name" {
  type = string
}

variable "env" {
  type = string
}

variable "base_ami_image" {
  type = string
}

variable "base_ami_image_owner" {
  type = string
}

variable "vpc_cidr" {
  type    = string
}

variable "subnet_cidrs" {
  type    = set(string)
}

variable "azs" {
  type    = set(string)
}

variable "base_domain_name" {
  type    = string
}

variable "domain_name" {
  type    = string
}

variable "ec2_ssh_key" {
  type = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "rds_instance_type" {
  description = "RDS instance type"
  type        = string
}

variable "autoscaling_health_check_type" {
  description = "either EC2 or ELB"
  type = string
}

variable "ssh_allowed_cidrs" {
  description = "CIDR blocks allowed to reach the EC2 instances over SSH (port 22). Defaults to the Reef jump-boxes; override for your own network."
  type        = list(string)
  default     = ["51.254.203.61/32", "46.62.159.127/32"]
}

variable "monitoring_allowed_cidrs" {
  description = "CIDR blocks allowed to reach the monitoring mTLS endpoint (port 10443). Defaults to the Reef monitoring hosts."
  type        = list(string)
  default     = ["138.68.147.48/32", "95.179.202.73/32"]
}
