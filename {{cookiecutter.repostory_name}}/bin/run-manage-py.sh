#!/bin/bash
if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi
docker-compose run --rm app sh -c "python manage.py $*"
