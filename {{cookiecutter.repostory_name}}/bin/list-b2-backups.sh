#!/bin/bash -eu

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

if [[ $# -ne 3 ]]; then
    echo "Usage: bin/list-b2-backups-b2.sh <B2_KEY_ID> <B2_KEY_SECRET> <B2_BUCKET_NAME>"
    echo "All arguments are required"
    exit 2
fi

IMAGE_NAME="{{ cookiecutter.repostory_name }}-backups-b2"
docker build --quiet -t "$IMAGE_NAME" tools/backup-b2

FILENAME=.backups/restore_from_b2.sql.gz

docker run \
  --mount type=bind,src="$(pwd)"/.backups,target=/root/.backups \
  --rm \
  --env BACKUP_B2_KEY_ID="$1" \
  --env BACKUP_B2_KEY_SECRET="$2" \
  "$IMAGE_NAME" ./list_backups.sh --long "$3"
