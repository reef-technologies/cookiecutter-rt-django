#!/bin/bash -eux

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
  . bin/backup-db.sh
else
  . bin/backup-db.sh
fi

date

EMAIL_CREDS="${EMAIL_HOST_USER}:${EMAIL_HOST_PASSWORD}@${EMAIL_HOST}:${EMAIL_PORT}" bin/emailhelper.py --to "$1" --subject "Backup of ${POSTGRES_DB}" -f "$target"

echo "Email sent successfully"
