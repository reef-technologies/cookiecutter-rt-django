data "aws_partition" "self" {}

resource "aws_ssm_parameter" "compose" {
  name = "/application/${var.name}/${var.env}/docker-compose.yml"
  type = "SecureString"
  value = <<EOF
version: '3.7'

services:
  app:
    image: ${var.ecr_base_url}/${var.ecr_image}
    init: true
    restart: always
    env_file: ./.env
    {% if cookiecutter.monitoring == 'y' %}
    environment:
      - PROMETHEUS_MULTIPROC_DIR=/prometheus-multiproc-dir
    {% endif %}
    volumes:
      - backend-static:/root/src/static
      - ./media:/root/src/media
    {% if cookiecutter.monitoring == 'y' %}
      - ./prometheus-multiproc-dir/app:$${PROMETHEUS_MULTIPROC_DIR}
    {% endif %}
    logging:
      driver: awslogs
      options:
        awslogs-region: ${var.region}
        awslogs-group: /aws/ec2/${var.name}-${var.env}-app
        awslogs-create-group: "true"

  {% if cookiecutter.monitoring == 'y' %}
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
        tag: {% raw %}'{###{.Name}###}'{% endraw %}

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
  {% endif %}

  nginx:
    image: 'ghcr.io/reef-technologies/nginx-rt:v1.0.0'
    restart: unless-stopped
    healthcheck:
      test: wget -q --spider http://0.0.0.0/admin/login || exit 1
    links:
      - app:app
      {% if cookiecutter.monitoring == 'y' %}
      - cadvisor:cadvisor
      - node-exporter:node-exporter
      {% endif %}
    command: nginx -g 'daemon off;'
    ports:
      {% if cookiecutter.monitoring == 'y' %}
      - 10443:10443
      {% endif %}
      - 8000:8000
    volumes:
      - ./nginx/templates:/etc/nginx/templates
      - ./nginx/config_helpers:/etc/nginx/config_helpers
      - backend-static:/srv/static:ro
      - ./media:/srv/media:ro
      - ./nginx/monitoring_certs:/etc/monitoring_certs
    logging:
      driver: awslogs
      options:
        awslogs-region: ${var.region}
        awslogs-group: /aws/ec2/${var.name}-${var.env}-nginx
        awslogs-create-group: "true"

volumes:
  backend-static:
EOF
}