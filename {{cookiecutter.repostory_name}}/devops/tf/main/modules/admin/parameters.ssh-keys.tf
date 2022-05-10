resource "aws_ssm_parameter" "ssh-keys" {
  name = "/application/${var.name}/${var.env}/.ssh/authorized_keys"
  type = "SecureString"
  value = <<EOF
ssh-ed25519 PUT YOUR KEY HERE!!! person@computer
EOF
}
