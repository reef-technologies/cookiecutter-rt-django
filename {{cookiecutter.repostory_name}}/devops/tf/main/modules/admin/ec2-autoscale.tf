locals {
  name_env    = var.env == "prod" ? var.name : "${var.name}-${var.env}"
  cloudinit   = <<EOM
#cloud-config
groups:
  - docker

system_info:
  default_user:
    groups: [docker]

write_files:
  - path: /home/ubuntu/installer.sh
    permissions: '0755'
    content: |
      apt-get clean && apt-get update && apt-get install -y ca-certificates curl gnupg lsb-release unzip jq rng-tools

      curl https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip -o awscliv2.zip
      unzip awscliv2.zip
      ./aws/install
      rm -rf ./aws ./awscliv2.zip

      curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
      echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
      apt-get update
      apt-get install -y docker-ce docker-ce-cli containerd.io
      gpasswd -a ubuntu docker
      mkdir -p /etc/docker/
      service docker restart

      curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
      chmod +x /usr/local/bin/docker-compose
  - path: /home/ubuntu/cloud-init.sh
    permissions: '0755'
    content: |
      #!/bin/bash

      export APP_NAME=${var.name}
      export APP_ENV=${var.env}

      aws ssm describe-parameters | jq -r '.Parameters[].Name' | grep "$APP_ENV" | sed "s/\/application.*$APP_ENV\///" | while read -r FILE; do
          mkdir -p $(dirname "$FILE");
          aws ssm get-parameter --name "/application/$APP_NAME/$APP_ENV/$FILE" --output text --with-decrypt --query 'Parameter.Value' | sed "s/###//g" > "$FILE";
      done

      source .envrc

      aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin "$AWS_ECR_BASE_URL"
      docker-compose up -d
runcmd:
  - chown -R ubuntu:ubuntu /home/ubuntu
  - cd /home/ubuntu/
  {% if cookiecutter.aws_use_packer == 'n' %}
  - "[ -f ./installer.sh ] && ./installer.sh"
  {% endif %}
  - sudo -u ubuntu ./cloud-init.sh
EOM
}

resource "aws_launch_template" "admin" {
  name          = local.name_env
  image_id      = var.base_ami_id
  instance_type = "t3.medium"

  iam_instance_profile {
    name = aws_iam_instance_profile.admin.name
  }

  disable_api_termination = false
  key_name                = aws_key_pair.rsa.key_name

  user_data = base64encode(local.cloudinit)

  block_device_mappings {
    device_name = "/dev/sda1"

    ebs {
      delete_on_termination = true
      encrypted = true
      volume_size = 20
    }
  }

  credit_specification {
    cpu_credits = "standard"
  }

  vpc_security_group_ids = [
    aws_security_group.internal.id
  ]
}

resource "aws_autoscaling_group" "admin" {
  name                = local.name_env
  desired_capacity    = 1
  max_size            = 1
  min_size            = 1
  vpc_zone_identifier = [var.subnets[0]]

  launch_template {
    id = aws_launch_template.admin.id
    version = "$Latest"
  }

  tag {
    key = "Name"
    propagate_at_launch = true
    value = local.name_env
  }

  target_group_arns = [
    aws_lb_target_group.admin.arn
  ]

  health_check_type = var.health_check_type
}
