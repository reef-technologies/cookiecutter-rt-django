#!/bin/sh

b2 authorize-account "$BACKUP_B2_KEY_ID" "$BACKUP_B2_KEY_SECRET"
b2 download-file-by-name "$BACKUP_B2_BUCKET" "$1" ".backups/$(basename "$1")"

