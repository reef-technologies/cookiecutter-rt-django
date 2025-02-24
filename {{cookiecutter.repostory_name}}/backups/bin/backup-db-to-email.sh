#!/bin/bash
set -eu

if [ ! -f "$1" ]; then
  echo "Pass existing backup file name as the first argument"
  find "$BACKUP_LOCAL_DIR" -name "*.dump.zstd" | sort -r
  exit 127
fi

date

EMAIL_CREDS="${EMAIL_HOST_USER}:${EMAIL_HOST_PASSWORD}@${EMAIL_HOST}:${EMAIL_PORT}" uv run emailhelper.py --from "${DEFAULT_FROM_EMAIL}" --to "${EMAIL_TARGET}" --subject "Database backup" -f "$1"

echo "Email sent successfully"