#!/bin/sh -eux
# Copyright 2020, Reef Technologies (reef.pl), All rights reserved.

DOCKER_BIN="$(command -v docker | true)"
DOCKER_COMPOSE_BIN="$(command -v docker-compose | true)"

if [ -x "${DOCKER_BIN}" ] && [ -x "${DOCKER_COMPOSE_BIN}" ]; then
    echo "\e[31mDocker and Docker Compose is already installed!\e[0m";
    exit 1;
fi

DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y apt-transport-https ca-certificates curl software-properties-common python3-pip

if [ ! -x "${DOCKER_BIN}" ]; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | apt-key add -
    add-apt-repository -y "deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable"
    apt-get -y install docker-ce
fi

if [ ! -x "${DOCKER_COMPOSE_BIN}" ]; then
    apt-get -y install docker-ce docker-compose
fi
