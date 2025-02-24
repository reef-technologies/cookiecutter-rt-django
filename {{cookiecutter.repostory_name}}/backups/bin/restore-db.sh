#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/common.sh"

if [[ $# -ne 1 ]]; then
    echo "Usage: ./restore-db.sh <FILE>"
    "${SCRIPT_DIR}"/list-backups.sh
    exit 2
fi

if [[ "$1" == b2://* || "$1" == b2id://* ]]; then
    export B2_APPLICATION_KEY_ID="$BACKUP_B2_KEY_ID"
    export B2_APPLICATION_KEY="$BACKUP_B2_KEY_SECRET"
    b2 cat "$1" | pg_restore -c -d "$DATABASE_URL"
else
    pg_restore -c -d "$DATABASE_URL" < "$1"
fi

echo 'restore finished'