#!/bin/bash -eux

set -o pipefail

# Update PATH in case docker-compose is installed via PIP
# and this script was invoked from e.g. cron
PATH=/usr/local/sbin:/usr/local/bin:$PATH

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .env

target="db_dump_$(date +%Y-%m-%d_%H%M%S).sql.gz"

if [[ "$DATABASE_URL" =~ "@db:" ]]; then
  DOCKER_NETWORK={{cookiecutter.repostory_name}}_default
else
  DOCKER_NETWORK=host
fi

docker run --rm --network $DOCKER_NETWORK postgres:9.6-alpine pg_dump -c "$DATABASE_URL" | gzip > "$target"

echo "$target"
