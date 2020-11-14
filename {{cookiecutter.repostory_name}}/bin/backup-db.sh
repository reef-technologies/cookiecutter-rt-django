#!/bin/bash -eux

# Update PATH in case docker-compose is installed via PIP
# and this script was invoked from e.g. cron
PATH=/usr/local/sbin:/usr/local/bin:$PATH

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .env

target="db_dump_$(date +%Y-%m-%d_%H%M%S).sql.gz"

if [[ "$DATABASE_URL" =~ "@db:" ]]; then
  docker run --rm --network {{cookiecutter.repostory_name}}_default postgres:9.6-alpine pg_dump "$DATABASE_URL" | gzip > "$target"
else
  docker run --rm --network host postgres:9.6-alpine pg_dump "$DATABASE_URL" | gzip > "$target"
fi
