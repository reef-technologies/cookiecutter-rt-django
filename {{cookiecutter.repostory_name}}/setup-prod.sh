#!/usr/bin/env bash
# Copyright 2017, Reef Technologies (reef.pl), All rights reserved.

PROJECT_DIR=`cd "$(dirname "${BASH_SOURCE[0]}")" && pwd`

# Set docker-compose.yml symlink
ln -sf docker-compose-prod.yml docker-compose.yml

# Set .env symlink
ln -sf .env-prod .env
