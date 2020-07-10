#!/usr/bin/env bash

# To debug uncomment this
#set -x
here=aws-sso
echo $here/scripts/deploy-to-current-environment.sh

export nounset=$(shopt -o nounset >/dev/null; echo $?)
set +o nounset
#set -o xtrace
if test -z "$xtrace" ; then
  export xtrace=$(shopt -o xtrace >/dev/null; echo $?)
fi
if test -z "$errexit" ; then
  export errexit=$(shopt -o errexit >/dev/null; echo $?)
fi

#export ROOT_DIR=$CI_PROJECT_DIR
#set +x
#cd $ROOT_DIR
#test 0 -eq $xtrace && set -x

export DEPLOY_TO_CURRENT_ACTION_SCRIPT=${DEPLOY_TO_CURRENT_ACTION_SCRIPT:-$SHARED_CI_SCRIPTS_DIR/push_layer_version.sh}

source $SHARED_CI_SCRIPTS_DIR/deploy-to-current-environment.sh
RC=$? ; test 0 -eq $RC || exit $RC

test 0 -eq $RC
