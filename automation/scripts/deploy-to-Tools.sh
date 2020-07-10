#!/usr/bin/env bash

export AWS_PROFILE=RStools
export AWS_DEFAULT_REGION=us-east-1
export APP=cicd_cdk
export CICD_ACCOUNT=tools

. ../../../apis/blocklist-api/automation/scripts/cdk.sh deploy --profile RStools \
  --require-approval=never --verbose \
  --parameters cdk-helper-cicd-cdk:CiCdArtifactStoreBucketArn=arn:aws:s3:::roadsync-tools-development-cicd-artifactstore-us-east-1 \
  --parameters cdk-helper-cicd-cdk:CiCdArtifactStoreBucketName=roadsync-tools-development-cicd-artifactstore-us-east-1