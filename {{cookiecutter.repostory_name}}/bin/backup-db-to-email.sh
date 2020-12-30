#!/bin/bash -eux

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

. .env

date

backup_file="$(bin/backup-db.sh)"

EMAIL_CREDS="${EMAIL_HOST_USER}:${EMAIL_HOST_PASSWORD}@${EMAIL_HOST}:${EMAIL_PORT}" bin/emailhelper.py --to "$1" --subject "Backup of ${POSTGRES_DB}" -f "$backup_file"

echo "Email sent successfully"

rm "$backup_file"
