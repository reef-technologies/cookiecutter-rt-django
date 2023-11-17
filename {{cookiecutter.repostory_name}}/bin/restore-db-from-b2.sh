#!/bin/bash -eu
set -o pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/common.sh"

if [[ $# -ne 1 ]]; then
    echo "Usage: bin/restore-db-from-b2.sh <B2_FILE_ID>"
    echo "All arguments are required"
    exit 2
fi

B2_FILE_ID="$1"

docker run --rm -i -e B2_APPLICATION_KEY="$BACKUP_B2_KEY_SECRET" -e B2_APPLICATION_KEY_ID="$BACKUP_B2_KEY_ID" \
  backblazeit/b2:3.13.0 cat "b2id://$1" | ${SCRIPT_DIR}/restore-db.sh -
