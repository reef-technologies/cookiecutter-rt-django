#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/common.sh"

echo "Local backups:"
find "$BACKUP_LOCAL_DIR" -name "*.dump.zstd" | sort -r

if [ -n "${B2_BUCKET}" ]; then
    echo "B2 backups:"
    uv run b2 ls --long "b2://$B2_BUCKET${B2_FOLDER:+/$B2_FOLDER/}"
fi