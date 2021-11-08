#!/bin/bash
if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

if [ "$1" = "detached" ]
  then
    docker-compose run --rm app sh -c "python manage.py ${@:2}"
elif
    docker-compose exec app sh -c "python manage.py $*"
fi
