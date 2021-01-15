#!/bin/sh -eu

b2 authorize-account "$BACKUP_B2_KEY_ID" "$BACKUP_B2_KEY_SECRET" && \
  b2 download-file-by-id "$B2_FILE_ID" "$1"

