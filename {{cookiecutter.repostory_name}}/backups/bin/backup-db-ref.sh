#!/bin/bash
# Takes a backup like backup-db.sh, checks that it can be read back and prints only what
# restore-db.sh needs to restore it.
set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/common.sh"

OUTPUT=$("${SCRIPT_DIR}"/backup-db.sh)
echo "$OUTPUT" >&2
TARGET_FILENAME=$(echo "$OUTPUT" | tail -n 1)

if [ -n "${B2_BUCKET}" ]; then
  REF="b2://${B2_BUCKET}/${B2_FOLDER:+${B2_FOLDER}/}${TARGET_FILENAME}"
  # uploading needs only the writeFiles capability, reading needs readFiles
  if ! uv run b2 file info "$REF" > /dev/null; then
    echo "ERROR: cannot read the backup $REF back from B2. The B2 application key needs the readFiles capability, see README.md, \"B2 cloud storage\"." >&2
    exit 1
  fi
else
  REF="${BACKUP_LOCAL_DIR}/${TARGET_FILENAME}"
  if ! pg_restore --list "$REF" > /dev/null; then
    echo "ERROR: the backup $REF is not a readable pg_dump archive." >&2
    exit 1
  fi
fi

echo "$REF"
