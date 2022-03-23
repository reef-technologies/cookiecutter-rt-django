{% raw %}
data "aws_partition" "self" {}

resource "aws_ssm_parameter" "compose" {
  name = "/application/${var.name}/${var.env}/docker-compose.yml"
  type = "SecureString"
  value = <<EOF
version: '3.7'

services:
  app:
    image: ${var.ecr_base_url}/${var.ecr_image}
    healthcheck:
      test: wget -q 127.0.0.1:8000/admin/login
    init: true
    restart: always
    env_file: ./.env
    logging:
      driver: awslogs
      options:
        awslogs-region: ${var.region}
        awslogs-group: /aws/ec2/${var.name}-${var.env}-app
        awslogs-create-group: "true"

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    logging: &exporter_logging
      driver: journald
      options:
        tag: '{###{.Name}###}'

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.40.0
    container_name: cadvisor
    privileged: true
    devices:
      - /dev/kmsg:/dev/kmsg
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker:/var/lib/docker:ro
      - /cgroup:/cgroup:ro
    restart: unless-stopped
    logging:
      <<: *exporter_logging

  nginx:
    image: 'ghcr.io/reef-technologies/nginx-rt:v1.0.0'
    restart: unless-stopped
    healthcheck:
      test: wget -q 0.0.0.0:80
    links:
      - cadvisor:cadvisor
      - node-exporter:node-exporter
      - app:app
    command: nginx -g 'daemon off;'
    ports:
      - 10443:10443
      - 8000:8000
    volumes:
      - ./reef_monitoring:/etc/certs
    logging:
      driver: awslogs
      options:
        awslogs-region: ${var.region}
        awslogs-group: /aws/ec2/${var.name}-${var.env}-nginx
        awslogs-create-group: "true"
EOF
}
{% endraw %}