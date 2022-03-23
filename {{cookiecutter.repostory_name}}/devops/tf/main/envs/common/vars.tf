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
