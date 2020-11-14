#!/bin/bash -eux

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .env

target="$1"

if [[ "$DATABASE_URL" =~ "@db:" ]]; then
  zcat "$target" | docker run -i --rm --network {{cookiecutter.repostory_name}}_default postgres:9.6-alpine psql "$DATABASE_URL"
else
  zcat "$target" | docker run -i --rm --network host postgres:9.6-alpine psql "$DATABASE_URL"
fi
