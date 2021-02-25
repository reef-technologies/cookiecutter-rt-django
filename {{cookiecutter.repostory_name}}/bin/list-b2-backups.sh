#!/bin/bash -eu

if [ "$(basename "$0")" == 'bin' ]; then
  cd ..
fi

if [[ $# -ne 3 ]]; then
    echo "Usage: bin/list-b2-backups-b2.sh <B2_KEY_ID> <B2_KEY_SECRET> <B2_BUCKET_NAME>"
    echo "All arguments are required"
    exit 2
fi

b2 authorize-account "$1" "$2"
b2 ls --long "$3"
