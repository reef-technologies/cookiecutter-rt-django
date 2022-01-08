#!/bin/sh -eux
# Copyright 2020, Reef Technologies (reef.pl), All rights reserved.

DOCKER_BIN="$(command -v docker || true)"
DOCKER_COMPOSE_BIN="$(command -v docker-compose || true)"
SENTRY_CLI="$(command -v sentry-cli || true)"
B2_CLI="$(command -v b2 || true)"
AWS_CLI="$(command -v aws || true)"
JQ_BIN="$(command -v jq || true)"

if [ -x "${DOCKER_BIN}" ] && [ -x "${DOCKER_COMPOSE_BIN}" ] && [ -x "${SENTRY_CLI}" ] && [ -x "${B2_CLI}" ] && [ -x "${AWS_CLI}" ] && [ -x "${JQ_BIN}" ]; then
    echo "\e[31mEverything required is already installed!\e[0m";
    exit 1;
fi

WORK_DIR="$(mktemp -d)"
if [ ! "${WORK_DIR}" ] || [ ! -d "${WORK_DIR}" ]; then
  echo "Could not create temp dir"
  exit 1
fi
cd "${WORK_DIR}"
cleanup() {
  rm -rf "${WORK_DIR}"
}
trap cleanup EXIT

DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y apt-transport-https ca-certificates curl software-properties-common python3-pip rng-tools

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

if [ ! -x "${AWS_CLI}" ]; then
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    ./aws/install
fi

if [ ! -x "${JQ_BIN}" ]; then
  curl -s --output /usr/local/bin/jq -L https://github.com/stedolan/jq/releases/download/jq-1.6/jq-linux64
  chmod a+x /usr/local/bin/jq
fi
