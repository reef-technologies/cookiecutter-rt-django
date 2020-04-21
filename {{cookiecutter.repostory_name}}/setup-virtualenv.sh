#!/usr/bin/env bash
# Copyright 2017, Reef Technologies (reef.pl), All rights reserved.

PROJECT_DIR=`cd "$(dirname "${BASH_SOURCE[0]}")" && pwd`

# Check if we are inside virtualenv
[[ ! -z $VIRTUAL_ENV ]] || { echo -e "\e[31mYou must run this script inside virtualenv!\e[0m"; exit 1; }

# Install pip packages
[[ -z `pip freeze` ]] || echo -e "\e[33mVirtualenv is not clean, already installed packages may be upgraded\e[0m"
echo "Installing pip development requirements"
pip install --upgrade -r "${PROJECT_DIR}/app/src/requirements.txt"


# Set default docker-compose.yml file
ln -sf dc-virtualenv.yml docker-compose.yml


# Backup .env file
[[ ! -f "${PROJECT_DIR}/.env" ]] || mv "${PROJECT_DIR}/.env" "${PROJECT_DIR}/.env~"

# Load .envrc from backup
[[ ! -f "${PROJECT_DIR}/.envrc~" ]] || mv "${PROJECT_DIR}/.envrc~" "${PROJECT_DIR}/.envrc"

# Create .envrc from template
[[ -f "${PROJECT_DIR}/.envrc" ]] || cp "${PROJECT_DIR}/.envrc.template" "${PROJECT_DIR}/.envrc"


# Enable direnv
eval "direnv allow"
