#!/bin/bash
set -xe

THIS_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
source "$THIS_DIR"/vars.sh

cd "$PROJECT_DIR"/app

echo "Deploying Backend: ${APP_NAME}"
docker push "${APP_OWNER}".dkr.ecr."${APP_REGION}".amazonaws.com/"${APP_NAME}":latest

# The ASG only exists after the env's `tf/main` has been applied at least once.
# On the very first deploy it isn't there yet, so skip the refresh instead of
# failing hard (the image is already in ECR for the first machine to pull).
ASG_EXISTS=$(aws autoscaling describe-auto-scaling-groups \
  --region "${APP_REGION}" \
  --auto-scaling-group-names "${APP_NAME}" \
  --query 'length(AutoScalingGroups)' --output text)

if [ "${ASG_EXISTS}" = "0" ]; then
  echo "Auto Scaling Group '${APP_NAME}' does not exist yet - skipping instance refresh."
  echo "This is expected on the first deploy; apply 'devops/tf/main/envs/${1}' to create it."
else
  aws autoscaling start-instance-refresh --region "${APP_REGION}" --auto-scaling-group-name "${APP_NAME}"
fi
