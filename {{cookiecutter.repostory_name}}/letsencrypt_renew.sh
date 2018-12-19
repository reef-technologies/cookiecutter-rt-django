#!/bin/bash -eux

echo "[$(date)] refreshing letsencrypt certificate..."

cd "$(dirname "$0")"

docker run -t --rm \
      -v "$PWD/letsencrypt/etc:/etc/letsencrypt" \
      -v "$PWD/letsencrypt/data:/data/letsencrypt" \
      deliverous/certbot \
      renew \
      --webroot --webroot-path=/data/letsencrypt

docker-compose kill -s HUP nginx

echo "[$(date)] ok"
