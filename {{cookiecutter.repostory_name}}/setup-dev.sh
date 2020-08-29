#!/usr/bin/env bash
# Copyright 2017, Reef Technologies (reef.pl), All rights reserved.

PROJECT_DIR=`cd "$(dirname "${BASH_SOURCE[0]}")" && pwd`

# Check if we are inside virtualenv
[[ ! -z $VIRTUAL_ENV ]] || { echo -e "\e[31mYou must run this script inside virtualenv!\e[0m"; exit 1; }

# Install pip packages
[[ -z `pip freeze` ]] || echo -e "\e[33mVirtualenv is not clean, already installed packages may be upgraded\e[0m"
echo "Installing pip development requirements"
pip install --upgrade pip
pip install --upgrade -r "${PROJECT_DIR}/app/src/requirements.txt"

# Set docker-compose.yml symlink
ln -sf docker-compose-dev.yml docker-compose.yml

# Set .env symlink
ln -sf .env-dev .env
