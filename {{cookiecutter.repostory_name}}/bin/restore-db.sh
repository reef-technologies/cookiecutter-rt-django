#!/bin/bash -eu
if [ "$(basename "$0")" == 'bin' ]; then
  . ../.env
else
  . .env
fi

target="$1"

if [ -n "$DATABASE_URL" ]; then
  zcat "$target" | docker run -i --rm postgres:9.6 psql -d "$DATABASE_URL"
else
  zcat "$target" | docker-compose exec -T db psql -U postgres "$POSTGRES_DB"
fi

echo 'restore finished'

