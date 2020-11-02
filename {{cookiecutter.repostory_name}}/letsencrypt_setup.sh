#!/bin/bash -eux

RELPATH="$(dirname "$0")"
ABSPATH="$(realpath "$RELPATH")"

cd "$ABSPATH"

source ./.env

docker run -it --rm \
      -v "$ABSPATH/letsencrypt/etc:/etc/letsencrypt" \
      -v "$ABSPATH/letsencrypt/data:/data/letsencrypt" \
      -p 80:80\
      deliverous/certbot \
      certonly \
      --standalone --preferred-challenges http\
      -d "$NGINX_HOST"

./letsencrypt_setup_crontab.sh

crontab -l

{% if cookiecutter.use_https != 'y' %}
echo ""
echo "Project was generated without https configured."
echo "Please remember to uncomment lines in envs/prod/docker-compose.yml and nginx/templates/default.conf.template"
{% endif %}
