#!/bin/bash -eu

set -o pipefail

# Update PATH in case docker-compose is installed via PIP
# and this script was invoked from e.g. cron
PATH=/usr/local/sbin:/usr/local/bin:$PATH

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .env
mkdir -p .backups
TARGET=".backups/db_dump_$(date +%Y-%m-%d_%H%M%S).sql.gz"

if [[ "$DATABASE_URL" =~ "@db:" ]]; then
  DOCKER_NETWORK={{cookiecutter.repostory_name}}_default
else
  DOCKER_NETWORK=host
fi

docker run --rm --network $DOCKER_NETWORK postgres:9.6-alpine pg_dump -c "$DATABASE_URL" | gzip > "$TARGET"
echo "$TARGET"

if [ -n "$EMAIL_HOST" ]; then
  bin/backup-db-to-email.sh "$TARGET" || true
fi

if [ -n "$BACKUP_B2_BUCKET" ]; then
  bin/backup-db-to-b2.sh "$TARGET" || true
fi

if [ -n "$BACKUP_ROTATE_KEEP_LAST" ]; then
  echo "Rotating backup files - keeping $BACKUP_ROTATE_KEEP_LAST last ones"
  lines=$(($BACKUP_ROTATE_KEEP_LAST+1))
  cd .backups
  ls -t1 | tail -n "+$lines" | xargs rm
  cd ..
fi


