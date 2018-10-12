#!/bin/bash -eu
if [ "$(basename "$0")" == 'bin' ]; then
  . ../.envrc
else
  . .envrc
fi

EMAIL_CREDS="${EMAIL_HOST_USER}:${EMAIL_HOST_PASSWORD}:${EMAIL_HOST}:${EMAIL_PORT}" bin/emailhelper.py --to "$1" --subject "Backup of ${POSTGRES_DB}" -f "$(bin/backup-db.sh)"

echo "Email sent successfully"
