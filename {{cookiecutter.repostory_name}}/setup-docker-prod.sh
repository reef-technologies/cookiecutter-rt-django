#!/usr/bin/env bash
# Copyright 2017, Reef Technologies (reef.pl), All rights reserved.

PROJECT_DIR=`cd "$(dirname "${BASH_SOURCE[0]}")" && pwd`
PROJECT_NAME=`basename "$PROJECT_DIR"`


# Set default docker-compose.yml file
ln -sf dc-prod.yml docker-compose.yml


# Disable direnv
eval "direnv deny" 2> /dev/null


# Backup .envrc file
[[ ! -f "${PROJECT_DIR}/.envrc" ]] || mv "${PROJECT_DIR}/.envrc" "${PROJECT_DIR}/.envrc~"

# Load .env from backup
[[ ! -f "${PROJECT_DIR}/.env~" ]] || mv "${PROJECT_DIR}/.env~" "${PROJECT_DIR}/.env"

# Create .env from template
[[ -f "${PROJECT_DIR}/.env" ]] || cp "${PROJECT_DIR}/.env.template" "${PROJECT_DIR}/.env"
