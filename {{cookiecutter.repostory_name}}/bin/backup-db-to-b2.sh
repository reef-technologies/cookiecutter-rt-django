#!/bin/bash -eu

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

if [ ! -f "$1" ]; then
  echo "Pass existing backup file name (with .backups/ directory name) as the first argument"
  exit 2
fi

IMAGE_NAME="{{ cookiecutter.repostory_name }}-backups-b2"
docker build --quiet -t "$IMAGE_NAME" tools/backup-b2

docker run \
  --mount type=bind,src="$(pwd)"/.backups,target=/root/.backups,readonly \
  --rm \
  --env-file=.env \
  "$IMAGE_NAME" ./send_backup.sh "$1"

