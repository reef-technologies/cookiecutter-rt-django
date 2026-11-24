#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/common.sh"

check_env_vars DATABASE_URL

TARGET_FILENAME="db_dump_$(date +%Y-%m-%d_%H%M%S).Fc.dump.zstd"

DUMP_DB_TO_STDOUT=(
  pg_dump -Fc --compress=zstd -c --if-exists "$DATABASE_URL"
)

if [ -n "${B2_BUCKET}" ]; then
  "${DUMP_DB_TO_STDOUT[@]}" | "${SCRIPT_DIR}"/backup-file-to-b2.sh - "${TARGET_FILENAME}"
  BACKUP="b2://${B2_BUCKET}/${B2_FOLDER:+${B2_FOLDER}/}${TARGET_FILENAME}"
else
  mkdir -p "$BACKUP_LOCAL_DIR"
  BACKUP="$BACKUP_LOCAL_DIR/$TARGET_FILENAME"
  "${DUMP_DB_TO_STDOUT[@]}" > "$BACKUP"

  if [ -n "${EMAIL_HOST:-}" ] && [ -n "${EMAIL_TARGET:-}" ]; then
    "${SCRIPT_DIR}"/backup-db-to-email.sh "${BACKUP}"
  fi
fi

# the last line of output is the argument restore-db.sh takes to restore this backup
echo "$BACKUP"
