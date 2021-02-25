#!/bin/sh -eux
# Copyright 2020, Reef Technologies (reef.pl), All rights reserved.

DOCKER_BIN="$(command -v docker || true)"
DOCKER_COMPOSE_BIN="$(command -v docker-compose || true)"
SENTRY_CLI="$(command -v sentry-cli || true)"
B2_CLI="$(command -v b2 || true)"

if [ -x "${DOCKER_BIN}" ] && [ -x "${DOCKER_COMPOSE_BIN}" ] && [ -x "${SENTRY_CLI}" ] && [ -x "${B2_CLI}" ]; then
    echo "\e[31mEverything required is already installed!\e[0m";
    exit 1;
fi

DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y apt-transport-https ca-certificates curl software-properties-common python3-pip

if [ ! -x "${SENTRY_CLI}" ]; then
  curl -sL https://sentry.io/get-cli/ | bash
fi

if [ ! -x "${B2_CLI}" ]; then
  curl -s --output /usr/local/bin/b2 -L https://github.com/Backblaze/B2_Command_Line_Tool/releases/latest/download/b2-linux
  chmod a+x /usr/local/bin/b2
fi

if [ ! -x "${DOCKER_BIN}" ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository -y "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
    apt-get -y install docker-ce
    usermod -aG docker $USER
fi

if [ ! -x "${DOCKER_COMPOSE_BIN}" ]; then
    apt-get -y install docker-ce docker-compose
fi


