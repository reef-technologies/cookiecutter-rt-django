locals {
  cert_dir = "../../files/monitoring"
  files    = fileset(local.cert_dir, "*.txt")

  certs = length(local.files) > 0 ? [for cert_file in local.files : {
    name: replace(cert_file, ".txt", "")
    content: "${local.cert_dir}/${cert_file}"
  }] : []
}

resource "aws_ssm_parameter" "certs" {
  count   = length(local.certs)
  name    = "/application/${var.name}/${var.env}/reef_monitoring/${local.certs[count.index].name}"
  type    = "SecureString"
  value   = file(local.certs[count.index].content)
}