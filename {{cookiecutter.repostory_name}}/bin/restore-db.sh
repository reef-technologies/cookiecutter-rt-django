#!/bin/bash -eux

set -o pipefail

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .env

target="$1"

if [[ "$DATABASE_URL" =~ "@db:" ]]; then
  DOCKER_NETWORK={{cookiecutter.repostory_name}}_default
else
  DOCKER_NETWORK=host
fi

zcat "$target" | docker run -i --rm --network $DOCKER_NETWORK postgres:9.6-alpine psql "$DATABASE_URL"

echo 'restore finished'
