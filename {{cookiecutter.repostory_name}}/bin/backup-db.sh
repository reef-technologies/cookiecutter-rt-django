#!/bin/bash -eu

set -o pipefail

# Update PATH in case docker-compose is installed via PIP
# and this script was invoked from e.g. cron
PATH=/usr/local/sbin:/usr/local/bin:$PATH

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .env

if [ -n "${SENTRY_DSN}" ]; then
  export SENTRY_DSN
  eval "$(sentry-cli bash-hook)"
fi

mkdir -p .backups
TARGET=".backups/db_dump_$(date +%Y-%m-%d_%H%M%S).sql.gz"

if [[ "$DATABASE_URL" =~ "@db:" ]]; then
  DOCKER_NETWORK={{cookiecutter.repostory_name}}_default
else
  DOCKER_NETWORK=host
fi

docker run --rm --network $DOCKER_NETWORK postgres:9.6-alpine pg_dump -Z 9 -c --if-exists "$DATABASE_URL" > "$TARGET"
echo "${TARGET}"

if [ -n "${BACKUP_B2_BUCKET}" ]; then
  bin/backup-db-to-b2.sh "${TARGET}"
fi

if [ -n "${EMAIL_HOST}" ] && [ -n "${EMAIL_TARGET}" ]; then
  bin/backup-db-to-email.sh "${TARGET}"
fi


if [ -n "${BACKUP_LOCAL_ROTATE_KEEP_LAST}" ]; then
  echo "Rotating backup files - keeping ${BACKUP_LOCAL_ROTATE_KEEP_LAST} last ones"
  bin/rotate-local-backups.py "${BACKUP_LOCAL_ROTATE_KEEP_LAST}"
fi


