#!/bin/bash
if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi
docker-compose exec app bash -c "python manage.py $*" 
