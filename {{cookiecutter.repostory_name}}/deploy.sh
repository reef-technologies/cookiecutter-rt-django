#!/bin/sh -eux
PRIMARY_IMAGE_HASH=$(docker-compose build app | tee /dev/tty \
    | sed '/^$/d' | grep "AS secondary-image" -B1 | head -1 | awk '{print $2}')
docker-compose build  # build the rest of images

SERVICES=$(docker-compose ps --services 2>&1 > /dev/stderr \
           | grep -v -e 'is not set' -e nginx -e db -e redis)

docker-compose stop $SERVICES
docker-compose up -d

docker-compose exec app python manage.py migrate

# Reloading nginx configuration without the process downtime
# so it won't terminate connections established between clients and nginx.
# In case of changes related to nginx in the compose file entire service
# needs to be restarted manually `docker-compose restart nginx`
docker-compose exec nginx nginx -s reload

docker images --quiet --filter=dangling=true \
    | grep -v $PRIMARY_IMAGE_HASH \
    | xargs --no-run-if-empty docker rmi \
    || true
