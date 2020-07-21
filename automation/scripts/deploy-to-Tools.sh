#!/usr/bin/env bash

export AWS_PROFILE=RStools
export AWS_DEFAULT_REGION=us-east-1
export APP=cicd_cdk
export CICD_ACCOUNT=tools

. ../../../apis/blocklist-api/automation/scripts/cdk.sh deploy --profile RStools \
  --output /tmp/cdk.out \
  --require-approval=never --verbose \
  --parameters aws-sso-cicd-cdk:CiCdArtifactStoreBucketArn=arn:aws:s3:::roadsync-tools-development-cicd-artifactstore-us-east-1 \
  --parameters aws-sso-cicd-cdk:CiCdArtifactStoreBucketName=roadsync-tools-development-cicd-artifactstore-us-east-1