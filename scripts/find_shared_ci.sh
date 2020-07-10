#!/usr/bin/env bash

export nounset=$(shopt -o nounset >/dev/null; echo $?)
set +o nounset
#set -o xtrace
if test -z "$xtrace" ; then
  export xtrace=$(shopt -o xtrace >/dev/null; echo $?)
fi
if test -z "$errexit" ; then
  export errexit=$(shopt -o errexit >/dev/null; echo $?)
fi

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
echo $here/scripts/find_cicd-shared.sh

export CI_PROJECT_DIR=${CI_PROJECT_DIR:-$PWD}

#echo set -x $here/scripts/find_shared_ci.sh
#set -x
#export xtrace=0

if test -z "$SHARED_CI_SCRIPTS_DIR" ; then
  # This constructs fails BAD under Gitlab CI ... possibly others. $0 == /usr/bin/bash ...
  #export DIR="$CI_PROJECT_SCRIPTS_DIR"
  #export ROOT_DIR="$(cd $DIR/.. 2>/dev/null; pwd)"

  export ROOT_DIR=$CI_PROJECT_DIR
  export SHARED_CI_ROOT_DIR=${SHARED_CI_ROOT_DIR:-ROOT_DIR}
  start=$SHARED_CI_ROOT_DIR
  while test "." != "$start" -a "/" != "$start" -a ! -z "$start" -a -z "$SHARED_CI_DIR" ; do
    if test -d "$start" -a -d "$start/cicd-shared" ; then
      export SHARED_CI_DIR="$(cd $start/cicd-shared 2>/dev/null; pwd)"
    else
      start=$(dirname $start)
    fi
  done
  export SHARED_CI_DIR=${SHARED_CI_DIR:-$ROOT_DIR/cicd-shared}
  export CICD_SHARED_DIR=${CICD_SHARED_DIR:-$SHARED_CI_DIR}
  export SHARED_CI_SCRIPTS_DIR="$SHARED_CI_DIR/scripts"
fi
test -d $SHARED_CI_DIR -a -d $SHARED_CI_SCRIPTS_DIR
RC=$? ; test 0 -eq $RC || { printf "\\e[31m\\e[40mWhere is cicd-shared? Ended with: [$SHARED_CI_DIR]\\e[0m\\e[40m"; exit $RC; }

test 0 -eq $RC
#exit 1
