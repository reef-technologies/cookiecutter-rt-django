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
docker run -it --rm --network "$DOCKER_NETWORK" postgres:18.7-alpine@sha256:0115267ab5a509022df9319c77be365cef335adb71556c75f60f5360ee247e71 psql "$DATABASE_URL"
