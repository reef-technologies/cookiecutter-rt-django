#!/bin/sh -eux
docker-compose build
docker-compose down -v
docker-compose up -d
docker-compose exec app python manage.py migrate
docker-compose exec app python manage.py collectstatic
docker images --quiet --filter=dangling=true | xargs --no-run-if-empty docker rmi || true
