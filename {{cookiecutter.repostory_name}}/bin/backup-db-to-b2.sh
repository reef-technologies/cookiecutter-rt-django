#!/bin/bash -e

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

if [ ! -e "$1" ]; then
  echo "Pass existing backup file name (with .backups/ directory name) as the first argument"
  exit 127
fi

CONTAINER_NAME="{{ cookiecutter.repostory_name }}-backups-b2"
docker build --quiet -t "$CONTAINER_NAME" tools/backup-b2

docker run \
  --mount type=bind,src="$(pwd)"/.backups,target=/root/.backups,readonly \
  --env-file=.env \
  "$CONTAINER_NAME" ./send_backup.sh "$1"


