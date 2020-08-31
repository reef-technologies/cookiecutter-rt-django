#!/bin/sh -eux
# Copyright 2020, Reef Technologies (reef.pl), All rights reserved.

# Build and tag the first image from multi-stage app Dockerfile
# to mark it as not dangling
docker build -t {{cookiecutter.django_project_name}}/app-build --target base-image -f app/Dockerfile  app

docker-compose build

SERVICES=$(docker-compose ps --services 2>&1 > /dev/stderr \
           | grep -v -e 'is not set' -e nginx -e db -e redis)

docker-compose stop $SERVICES
docker-compose up -d

docker-compose exec -T app python manage.py migrate

# Reloading nginx configuration without the process downtime
# so it won't terminate connections established between clients and nginx.
# In case of changes related to nginx in the compose file entire service
# needs to be restarted manually `docker-compose restart nginx`
docker-compose exec -T nginx nginx -s reload

# Clean all dangling images
docker images --quiet --filter=dangling=true \
    | xargs --no-run-if-empty docker rmi \
    || true
