#!/bin/bash -eux

RELPATH="$(dirname "$0")"
ABSPATH="$(realpath "$RELPATH")"

cd "$ABSPATH"

source ./.env

docker-compose up -d nginx-letsencrypt

docker run -it --rm \
      -v "$ABSPATH/letsencrypt/etc:/etc/letsencrypt" \
      -v "$ABSPATH/letsencrypt/data:/data/letsencrypt" \
      deliverous/certbot \
      certonly \
      --standalone --preferred-challenges http\
      -d "$NGINX_HOST"

./letsencrypt_setup_crontab.sh

crontab -l

{% if cookiecutter.use_https == 'n'%}
echo ""
echo "Project was generated without https configured."
echo "Please remember to uncomment lines in dc-prod.yml and nginx/conf/default.template"
{% endif %}