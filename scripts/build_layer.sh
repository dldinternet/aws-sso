#!/usr/bin/env bash

# To debug uncomment this
#set -x
#export xtrace=0

# This does not work without BASH
if test -z "${BASH_VERSION}" ; then
  /usr/bin/env bash "$0" $*
  exit $?
fi

if test $((0 + $(echo ${BASH_VERSION:-0} | cut -d . -f 1) )) -lt 4 ; then
  echo "Your Bash($BASH) version is ${BASH_VERSION:-0} and you need >= 4.0.0"
  if test -f /usr/local/bin/bash ; then
    /usr/local/bin/bash "$0" $*
    exit $?
  fi
fi
here=aws-sso
echo $here/scripts/build_layer.sh
if test -d ~/.aws -a -f ~/.aws/credentials -a -f ~/.aws/config ; then
  export AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-us-east-1}
  export AWS_PROFILE=${AWS_PROFILE:-RSdevelop}
else
  echo "WARNING: Depending on instance profile or STS assumed role credentials!"
fi
export BUCKET_NAME=${BUCKET_NAME:-roadsync-tools-samclisource-us-east-1}
export KEEP_BUILD_DIR=yes
export DISABLE_TAG_VERSION=yes

#export AUTO_BUMP2VERSION=No
export nounset=$(shopt -o nounset >/dev/null; echo $?)
set +o nounset
shopt -o errexit >/dev/null
export errexit=$?
set +o errexit

export CI_PROJECT_DIR=${CI_PROJECT_DIR:-$PWD}
export CI_PROJECT_SCRIPTS_DIR=${CI_PROJECT_SCRIPTS_DIR:-$CI_PROJECT_DIR/scripts}
source "$CI_PROJECT_SCRIPTS_DIR/find_shared_ci.sh"
RC=$? ; test 0 -eq $RC || exit $RC

#copper $here/scripts/build_layer.sh
#set -x
#export xtrace=0

source "$CI_PROJECT_SCRIPTS_DIR/ci-before_script.rc"
RC=$? ; test 0 -eq $RC || exit $RC

export DONT_PACKAGE_ARTIFACT_FILE=yes
export DEPLOY_TO_CURRENT_ACTION_SCRIPT="$SHARED_CI_SCRIPTS_DIR/build_layer.sh"
source $CI_PROJECT_SCRIPTS_DIR/deploy-to-current-environment.sh
RC=$? ; test 0 -eq $RC || exit $RC

#set -x
set -o errexit # Down here we get strict again
export LOCAL_DIST_DIR=${LOCAL_DIST_DIR:-$LOCAL_BUILD_DIR/dist}
if test -f $PACKAGE_ARTIFACT_FILE ; then
  green "Found $PACKAGE_ARTIFACT_FILE :)"
else
  orange "MIA: $PACKAGE_ARTIFACT_FILE - do not need it"
  rm $LOCAL_BUILD_DIR/.python-version 2>/dev/null || false
  cd $LOCAL_BUILD_DIR
  . venv/bin/activate
  export PYTHONPATH=$LOCAL_BUILD_DIR/python
  pip install -r ../requirements-whl.txt >>$LOCAL_BUILD_DIR/pip.requirements-whl.log
  copper `pwd`
  copper zip $PACKAGE_ARTIFACT_FILE python
  test -f $PACKAGE_ARTIFACT_FILE? && green $PACKAGE_ARTIFACT_FILE?
  cd $CI_PROJECT_DIR
fi

test 0 -eq $RC
