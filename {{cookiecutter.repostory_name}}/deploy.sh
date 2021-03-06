#!/bin/sh -eux
# Copyright 2020, Reef Technologies (reef.pl), All rights reserved.

if [ ! -f ".env" ]; then
    echo "\e[31mPlease setup the environment first!\e[0m";
    exit 1;
fi

docker-compose build

# Tag the first image from multi-stage app Dockerfile to mark it as not dangling
BASE_IMAGE=$(docker images --quiet --filter="label=builder=true" | head -n1)
docker image tag ${BASE_IMAGE} {{cookiecutter.django_project_name}}/app-builder

SERVICES=$(docker-compose ps --services 2>&1 > /dev/stderr \
           | grep -v -e 'is not set' -e nginx -e db -e redis)

docker-compose stop $SERVICES
docker-compose up -d

docker-compose exec -T app python manage.py wait_for_database
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
