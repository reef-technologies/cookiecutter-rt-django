#!/bin/bash -eu
set -o pipefail
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
source "${SCRIPT_DIR}/common.sh"

target="$1"

DOCKER_NETWORK=$(get_db_docker_network)

zcat "$target" | docker run -i --rm --network $DOCKER_NETWORK postgres:14.0-alpine psql "$DATABASE_URL"

echo 'restore finished'
