#!/bin/bash -eu
if [ "$(basename "$0")" == 'bin' ]; then
  . ../.envrc
else
  . .envrc
fi

target="$1"

gunzip < "$target" | docker exec -i {{cookiecutter.django_project_name}}_db_1 psql -U postgres
