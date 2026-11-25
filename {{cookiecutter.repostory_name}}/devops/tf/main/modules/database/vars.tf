variable "name" {}
variable "env" {}

variable "vpc_id" {}
variable "vpc_cidr" {}
variable "subnets" {}
variable "azs" {}
variable "instance_type" {}
variable "instance_type_read_replica" {}

variable "create_readreplica" {
    type        = bool
    description = "Create readreplica? (true/false) default: false"
    default     = false
}

