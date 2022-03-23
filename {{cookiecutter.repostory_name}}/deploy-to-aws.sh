#!/bin/bash -e

./devops/scripts/build-backend.sh $1
./devops/scripts/deploy-backend.sh $1