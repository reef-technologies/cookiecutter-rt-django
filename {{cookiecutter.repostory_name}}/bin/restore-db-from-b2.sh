#!/bin/bash -eu

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

if [[ $# -ne 3 ]]; then
    echo "Usage: bin/restore-db-from-b2.sh <B2_KEY_ID> <B2_KEY_SECRET> <B2_FILE_ID>"
    echo "All arguments are required"
    exit 2
fi

FILENAME=.backups/restore_from_b2.sql.gz

b2 authorize-account "$1" "$2"
b2 download-file-by-id "$3" "$FILENAME"
bin/restore-db.sh "$FILENAME"
