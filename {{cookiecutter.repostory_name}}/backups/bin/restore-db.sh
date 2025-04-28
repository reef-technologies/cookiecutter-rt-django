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
    uv run b2 cat "$1" | pg_restore -c -d "$DATABASE_URL"
else
    pg_restore -c -d "$DATABASE_URL" < "$1"
fi

echo 'restore finished'