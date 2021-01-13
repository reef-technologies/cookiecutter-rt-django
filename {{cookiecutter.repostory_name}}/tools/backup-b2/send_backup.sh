#!/bin/sh

b2 authorize-account "$BACKUP_B2_KEY_ID" "$BACKUP_B2_KEY_SECRET" && \
  b2 upload-file "$BACKUP_B2_BUCKET" "$1" "$(basename "$1")"
