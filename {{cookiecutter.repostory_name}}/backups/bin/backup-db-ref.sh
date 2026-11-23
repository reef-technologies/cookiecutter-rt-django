#!/bin/bash
# Takes a backup like backup-db.sh and prints only what restore-db.sh needs to restore it.
set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/common.sh"

OUTPUT=$("${SCRIPT_DIR}"/backup-db.sh)
echo "$OUTPUT" >&2
TARGET_FILENAME=$(echo "$OUTPUT" | tail -n 1)

if [ -n "${B2_BUCKET}" ]; then
  echo "b2://${B2_BUCKET}/${B2_FOLDER:+${B2_FOLDER}/}${TARGET_FILENAME}"
else
  echo "${BACKUP_LOCAL_DIR}/${TARGET_FILENAME}"
fi
