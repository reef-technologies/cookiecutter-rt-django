#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/common.sh"

check_env_vars B2_APPLICATION_KEY_ID B2_APPLICATION_KEY B2_BUCKET

if [ "$1" == "-" ]; then
  B2_FILENAME="$2"
  [ -n "$B2_FILENAME" ] || (echo "Pass backup file name as the second argument if stdin was provided as data source">&2; exit 2)
elif [ ! -f "$1" ]; then
  echo "Pass existing backup file name as the first argument"
  exit 2
else
  B2_FILENAME="$(basename "$1")"
fi

if [ -n "${B2_FOLDER:-}" ]; then
  B2_FILENAME="$B2_FOLDER/$B2_FILENAME"
fi

uv run b2 file upload "$B2_BUCKET" "$1" "$B2_FILENAME"
