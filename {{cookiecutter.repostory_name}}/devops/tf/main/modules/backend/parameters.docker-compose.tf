data "aws_partition" "self" {}

resource "aws_ssm_parameter" "compose" {
  name = "/application/${var.name}/${var.env}/docker-compose.yml"
  type = "SecureString"
  # The compose file is larger than the 4 KB standard-tier limit once all
  # services are enabled, so use the advanced tier (8 KB).
  tier  = "Advanced"
  value = templatefile("../../files/docker-compose.yml", {
    name              = var.name
    env               = var.env
    region            = var.region
    ecr_base_url      = var.ecr_base_url
    ecr_image         = var.ecr_image
    ecr_backups_image = var.ecr_backups_image
  })
}

{% if cookiecutter.observability %}
resource "aws_ssm_parameter" "alloy_config" {
  name  = "/application/${var.name}/${var.env}/alloy/config.alloy"
  type  = "SecureString"
  value = file("../../files/alloy/config.alloy")
}
{% endif %}