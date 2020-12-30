#!/bin/bash

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .env

if [[ "$DATABASE_URL" =~ "@db:" ]]; then
  DOCKER_NETWORK={{cookiecutter.repostory_name}}_default
else
  DOCKER_NETWORK=host
fi

# this works even if `app` container doesn't have psql installed (where `bin/run-manage-py.sh dbshell` fails)
docker run -it --rm --network $DOCKER_NETWORK postgres:9.6-alpine psql "$DATABASE_URL"
