#!/usr/bin/env bash
# Copyright 2017, Reef Technologies (reef.pl), All rights reserved.

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV_DIR="./envs/dev"
# shellcheck disable=SC2164
cd "${PROJECT_DIR}"

# Workaround for PDM which sometimes creates a 3.10 venv
# https://github.com/pdm-project/pdm/issues/2789
if [[ ! -d ".venv" ]]; then
    python3.11 -m venv .venv
fi

# Create a lock file if doesn't exist
if [[ ! -f "pdm.lock" ]]; then
    pdm lock --group :all
fi
# Install Python dependencies
pdm sync --group :all

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
