resource "aws_key_pair" "rsa" {
  key_name   = "${var.name}-${var.env}-key"
  public_key = var.ec2_ssh_key
}