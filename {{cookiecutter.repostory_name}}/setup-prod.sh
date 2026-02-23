#!/usr/bin/env bash
# Copyright 2017, Reef Technologies (reef.pl), All rights reserved.

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENV_DIR="./envs/prod"
# shellcheck disable=SC2164
cd "${PROJECT_DIR}"

# Create .env from the template if doesn't exist
if [[ ! -f "${ENV_DIR}/.env" ]]; then
    cp "${ENV_DIR}/.env.template" "${ENV_DIR}/.env"
fi

{% if cookiecutter.vulnerabilities_scanning %}
# Create .vuln.env from the template if doesn't exist
if [[ ! -f "${ENV_DIR}/.vuln.env" ]]; then
    cp "${ENV_DIR}/.vuln.env.template" "${ENV_DIR}/.vuln.env"
fi
ln -sf "${ENV_DIR}/.vuln.env" .vuln.env
{% endif %}

# Set symlinks
ln -sf "${ENV_DIR}/.env" .env
ln -sf "${ENV_DIR}/docker-compose.yml" docker-compose.yml
# shellcheck disable=SC2164
cd "${PROJECT_DIR}/app/"
ln -sf "${ENV_DIR}/Dockerfile" Dockerfile
ln -sf ".${ENV_DIR}/entrypoint.sh" src/entrypoint.sh
