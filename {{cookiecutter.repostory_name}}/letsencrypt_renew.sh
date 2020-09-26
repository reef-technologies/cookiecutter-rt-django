#!/bin/bash -eux

# Update PATH in case docker-compose is installed via PIP
# and this script was invoked from e.g. cron
PATH=/usr/local/sbin:/usr/local/bin:$PATH

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
