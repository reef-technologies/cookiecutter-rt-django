#!/bin/bash -xe

THIS_DIR=`cd "$(dirname "${BASH_SOURCE[0]}")" && pwd`
source $THIS_DIR/vars.sh

cd "$PROJECT_DIR"/app

echo "Deploying Backend: ${APP_NAME}"
docker push ${APP_OWNER}.dkr.ecr.${APP_REGION}.amazonaws.com/${APP_NAME}:latest

echo "Sending slack notification"
commits=`git log --format=format:%H,%s`
commits=${commits//\`/\'}
docker run --rm ${APP_NAME} sh -c "python bin/notify.py --parse -m \"$commits\""

aws autoscaling start-instance-refresh --region ${APP_REGION} --auto-scaling-group-name ${APP_NAME}
