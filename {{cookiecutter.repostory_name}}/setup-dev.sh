#!/usr/bin/env bash
# Copyright 2017, Reef Technologies (reef.pl), All rights reserved.

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV_DIR="./envs/dev"
# shellcheck disable=SC2164
cd "${PROJECT_DIR}"

if [[ ! -d ".venv" ]]; then
    python3.11 -m venv .venv
fi

# Create a lock file if doesn't exist
if [[ ! -f "uv.lock" ]]; then
    uv lock
fi
# Install Python dependencies
uv sync --all-groups

# Create .env from the template if doesn't exist
if [[ ! -f "${ENV_DIR}/.env" ]]; then
    cp "${ENV_DIR}/.env.template" "${ENV_DIR}/.env"
fi

# Set symlinks
ln -sf "${ENV_DIR}/.env" .env
ln -sf "${ENV_DIR}/docker-compose.yml" docker-compose.yml

# shellcheck disable=SC2164
cd "${PROJECT_DIR}/app/"
if [[ -L "Dockerfile" ]]; then
    unlink Dockerfile
fi
if [[ -L "src/entrypoint.sh" ]]; then
    unlink src/entrypoint.sh
fi
