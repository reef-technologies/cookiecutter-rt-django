#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/common.sh"

echo "Local backups:"
find "$BACKUP_LOCAL_DIR" -name "*.dump.zstd" | sort -r

if [ -n "${BACKUP_B2_BUCKET}" ]; then
    export B2_APPLICATION_KEY_ID="$BACKUP_B2_KEY_ID"
    export B2_APPLICATION_KEY="$BACKUP_B2_KEY_SECRET"
    echo "B2 backups:"
    uv run b2 ls --long "b2://$BACKUP_B2_BUCKET"
fi