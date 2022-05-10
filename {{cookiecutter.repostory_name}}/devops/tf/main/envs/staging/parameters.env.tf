locals {
  ecr_base_url = "${data.aws_caller_identity.env.account_id}.dkr.ecr.${var.region}.amazonaws.com"
  ecr_image    = "${var.name}-${var.env}:latest"
}

resource "random_uuid" "random_uuid" {}

resource "aws_ssm_parameter" "envrc" {
  name  = "/application/${var.name}/${var.env}/.envrc"
  type  = "SecureString"
  value = <<EOF
export APP_NAME=${var.name}
export APP_ENV=${var.env}
export AWS_ACCOUNT_ID=${data.aws_caller_identity.env.account_id}
export AWS_ECR_BASE_URL=${local.ecr_base_url}
export AWS_ECR_TAG=${local.ecr_image}
EOF
}


resource "aws_ssm_parameter" "env" {
  name  = "/application/${var.name}/${var.env}/.env"
  type  = "SecureString"
  value = <<EOF
ENV=prod
NGINX_HOST=localhost
DEBUG=on
SECRET_KEY=${random_uuid.random_uuid.result}
POSTGRES_DB=${module.database.name}
POSTGRES_USER=${module.database.user}
POSTGRES_PASSWORD=${module.database.password}
DATABASE_URL=${module.database.connection_string}

SENTRY_DSN=
HTTPS_REDIRECT=n
HTTPS_PROXY_HEADER=X_SCHEME
CSP_ENABLED=n
CSP_REPORT_ONLY=n
CSP_REPORT_URL=
CSP_DEFAULT_SRC="'none'"
CSP_SCRIPT_SRC="'self'"
CSP_STYLE_SRC="'self'"
CSP_FONT_SRC="'self'"
CSP_IMG_SRC="'self'"
CSP_MEDIA_SRC="'self'"
CSP_OBJECT_SRC="'self'"
CSP_FRAME_SRC="'self'"
CSP_CONNECT_SRC="'self'"
CSP_CHILD_SRC="'self'"
CSP_MANIFEST_SRC="'self'"
CSP_WORKER_SRC="'self'"
CSP_BLOCK_ALL_MIXED_CONTENT=y
CSP_EXCLUDE_URL_PREFIXES=
BACKUP_B2_BUCKET=
BACKUP_B2_KEY_ID=
BACKUP_B2_KEY_SECRET=
BACKUP_LOCAL_ROTATE_KEEP_LAST=
EOF
}