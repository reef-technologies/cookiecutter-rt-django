#!/bin/bash

. .env

# this works even if `app` container doesn't have psql installed (where `bin/run-manage-py.sh dbshell` fails)
docker-compose exec db psql --dbname="$POSTGRES_DB" -U postgres
