#!/bin/bash
set -xe

THIS_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$THIS_DIR"/vars.sh

cd "$PROJECT_DIR"

DATE_UTC=$(date -u)
TIMESTAMP_UTC=$(date +%s)
GIT_SHA=${GIT_SHA:-$(git rev-parse --short HEAD 2>/dev/null || printf "%s" "local")}

echo "Building Backend: ${APP_NAME}"

./setup-prod.sh

aws ecr get-login-password --region "${APP_REGION}" | docker login --username AWS --password-stdin "${APP_OWNER}".dkr.ecr."${APP_REGION}".amazonaws.com

DOCKER_BUILDKIT=1 docker build \
  -f app/Dockerfile \
  --progress plain \
  --platform linux/amd64 \
  -t "${APP_NAME}" \
  --build-arg GIT_SHA="$GIT_SHA" \
  --label build_date_utc="$DATE_UTC" \
  --label build_timestamp_utc="$TIMESTAMP_UTC" \
  --label git_commit_hash="$GIT_SHA" \
  .
docker tag "${APP_NAME}":latest "${APP_OWNER}".dkr.ecr."${APP_REGION}".amazonaws.com/"${APP_NAME}":latest
docker tag "${APP_NAME}":latest "${APP_OWNER}".dkr.ecr."${APP_REGION}".amazonaws.com/"${APP_NAME}":"${GIT_SHA}"

docker push "${APP_OWNER}".dkr.ecr."${APP_REGION}".amazonaws.com/"${APP_NAME}":"${GIT_SHA}"
