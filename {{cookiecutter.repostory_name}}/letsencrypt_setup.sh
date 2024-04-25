#!/bin/bash
set -eux
RELPATH="$(dirname "$0")"
ABSPATH="$(realpath "$RELPATH")"

cd "$ABSPATH"

source ./.env
mkdir -p "$ABSPATH/letsencrypt/etc/dhparams"

docker run -it --rm \
      -v "$ABSPATH/letsencrypt/etc:/etc/letsencrypt" \
      alpine/openssl \
      dhparam -out /etc/letsencrypt/dhparams/dhparam.pem 2048

docker run --entrypoint certbot -it --rm \
      -v "$ABSPATH/letsencrypt/etc:/etc/letsencrypt" \
      -p 80:80\
      ghcr.io/reef-technologies/nginx-rt:v1.2.2 \
      certonly \
      --standalone --preferred-challenges http\
      -d "$NGINX_HOST" -d "www.$NGINX_HOST"
