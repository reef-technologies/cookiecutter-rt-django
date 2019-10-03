#!/bin/sh -eux
PRIMARY_IMAGE_HASH=$(docker-compose build app | tee /dev/tty \
    | sed '/^$/d' | grep "AS secondary-image" -B1 | head -1 | awk '{print $2}')
docker-compose build  # build the rest of images
docker-compose down -v --remove-orphans
docker-compose up -d
docker-compose exec app python manage.py migrate
docker-compose exec app python manage.py collectstatic
docker images --quiet --filter=dangling=true \
    | grep -v $PRIMARY_IMAGE_HASH \
    | xargs --no-run-if-empty docker rmi \
    || true
