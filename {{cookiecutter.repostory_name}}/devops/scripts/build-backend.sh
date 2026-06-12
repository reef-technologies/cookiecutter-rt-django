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
ECR_BASE="${APP_OWNER}".dkr.ecr."${APP_REGION}".amazonaws.com

docker tag "${APP_NAME}":latest "${ECR_BASE}"/"${APP_NAME}":latest
docker tag "${APP_NAME}":latest "${ECR_BASE}"/"${APP_NAME}":"${GIT_SHA}"

# Push both tags. cloud-init pulls ":latest" on first boot, so it must exist in
# ECR already - pushing only the SHA tag leaves the first machine with nothing to pull.
docker push "${ECR_BASE}"/"${APP_NAME}":latest
docker push "${ECR_BASE}"/"${APP_NAME}":"${GIT_SHA}"

# Build and push the backups image. On AWS the backups service runs from ECR
# (there is no build context on the EC2 host), so it needs its own repository.
BACKUPS_IMAGE="${APP_NAME}-backups"
DOCKER_BUILDKIT=1 docker build \
  -f backups/Dockerfile \
  --progress plain \
  --platform linux/amd64 \
  -t "${BACKUPS_IMAGE}" \
  --label build_date_utc="$DATE_UTC" \
  --label build_timestamp_utc="$TIMESTAMP_UTC" \
  --label git_commit_hash="$GIT_SHA" \
  backups/
docker tag "${BACKUPS_IMAGE}":latest "${ECR_BASE}"/"${BACKUPS_IMAGE}":latest
docker tag "${BACKUPS_IMAGE}":latest "${ECR_BASE}"/"${BACKUPS_IMAGE}":"${GIT_SHA}"

docker push "${ECR_BASE}"/"${BACKUPS_IMAGE}":latest
docker push "${ECR_BASE}"/"${BACKUPS_IMAGE}":"${GIT_SHA}"
