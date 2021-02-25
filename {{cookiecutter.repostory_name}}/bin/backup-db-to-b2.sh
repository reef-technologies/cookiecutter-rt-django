#!/bin/bash -eu

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

if [ ! -f "$1" ]; then
  echo "Pass existing backup file name (with .backups/ directory name) as the first argument"
  exit 2
fi

. .env

b2 authorize-account "$BACKUP_B2_KEY_ID" "$BACKUP_B2_KEY_SECRET"
b2 upload-file "$BACKUP_B2_BUCKET" "$1" "$(basename "$1")"



