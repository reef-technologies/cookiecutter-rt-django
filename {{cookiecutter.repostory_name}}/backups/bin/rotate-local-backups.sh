#!/bin/bash
if [ -n "${BACKUP_LOCAL_ROTATE_KEEP_LAST:-}" ]; then
    echo "Rotating backup files - keeping ${BACKUP_LOCAL_ROTATE_KEEP_LAST} last ones"
    files_to_delete=$(find /var/backups -name "*.dump.zstd" | sort -r | tail -n "+${BACKUP_LOCAL_ROTATE_KEEP_LAST}")
    echo "$files_to_delete" | xargs --no-run-if-empty rm
    echo "Removed:"
    echo "$files_to_delete"
else
    echo "BACKUP_LOCAL_ROTATE_KEEP_LAST is not set, skipping backup rotation"
fi