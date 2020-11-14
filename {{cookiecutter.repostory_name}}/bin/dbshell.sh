#!/bin/bash

. .env

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .env

# this works even if `app` container doesn't have psql installed (where `bin/run-manage-py.sh dbshell` fails)
if [[ "$DATABASE_URL" =~ "@db:" ]]; then
  docker run -it --rm --network {{cookiecutter.repostory_name}}_default postgres:9.6-alpine psql "$DATABASE_URL"
else
  docker run -it --rm --network host postgres:9.6-alpine psql "$DATABASE_URL"
fi
