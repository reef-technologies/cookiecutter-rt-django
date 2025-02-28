#!/bin/sh
# Copyright 2024, Reef Technologies (reef.pl), All rights reserved.
set -eux

if [ ! -f ".env" ]; then
    echo "\e[31mPlease setup the environment first!\e[0m";
    exit 1;
fi

docker compose build

# Tag the first image from multi-stage app Dockerfile to mark it as not dangling
BASE_IMAGE=$(docker images --quiet --filter="label=builder=true" | head -n1)
docker image tag "${BASE_IMAGE}" {{cookiecutter.django_project_name}}/app-builder

# collect static files to external storage while old app is still running
# docker compose run --rm app sh -c "python manage.py collectstatic --no-input"

SERVICES=$(docker compose ps --services 2>/dev/null \
           | grep -v -e 'is not set' -e db -e redis)

# shellcheck disable=2086
docker compose stop $SERVICES

docker compose up -d db  # in case it hasn't been launched before
# backup db before any database changes
docker compose run --rm backups ./backup-db.sh
# start the app container only in order to perform migrations
docker compose run --rm app sh -c "python manage.py wait_for_database --timeout 10; python manage.py migrate"

# start everything
docker compose up -d

# Clean all dangling images
docker images --quiet --filter=dangling=true \
    | xargs --no-run-if-empty docker rmi \
    || true
