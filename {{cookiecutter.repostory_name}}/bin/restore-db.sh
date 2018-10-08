#!/bin/bash
if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .envrc

target="$1"

gunzip < "$target" | docker exec -i {{cookiecutter.django_project_name}}_db_1 psql -U postgres

echo "$target"
