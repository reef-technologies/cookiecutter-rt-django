[ "$1" != "staging" ] && [ "$1" != "prod" ] &&  echo "Please provide environment name to deploy: staging or prod" && exit 1;

PROJECT_DIR=`cd "$(dirname "${BASH_SOURCE[0]}")" && pwd`/../../

[ "$1" != "prod" ] && APP_SUFFIX="-$1"

APP_OWNER=$(aws sts get-caller-identity --query "Account" --output text)
APP_REGION="{{ cookiecutter.aws_region }}"
APP_NAME="{{ cookiecutter.aws_project_name }}${APP_SUFFIX}"
CLOUDFRONT_BUCKET="${APP_NAME}-spa${APP_SUFFIX}"