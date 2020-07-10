#!/usr/bin/env bash

echo builder-images/scripts/tag_version.sh
export nounset=$(shopt -o nounset >/dev/null; echo $?)
set +o nounset
shopt -o errexit >/dev/null
export errexit=$?
set +o errexit

#set -x
#export xtrace=0

export CI_PROJECT_DIR=${CI_PROJECT_DIR:-$PWD}
export CI_PROJECT_SCRIPTS_DIR=${CI_PROJECT_SCRIPTS_DIR:-$CI_PROJECT_DIR/scripts}
source "$CI_PROJECT_SCRIPTS_DIR/find_shared_ci.sh"
RC=$? ; test 0 -eq $RC || exit $RC


source "$CI_PROJECT_SCRIPTS_DIR/ci-before_script.rc"
RC=$? ; test 0 -eq $RC || exit $RC


function bump_version_rev {
  bump2version --verbose --commit --tag rev --allow-dirty $*
  return $?
}

test -z "$BUMP_VERSION_FUNC" && BUMP_VERSION_FUNC=bump_version_rev

# Let's take care of our submodules ...
if test -z "$CI_JOB_ID" ; then
  # Let's take care of our submodules ...
  if test -f .gitmodules; then
    # Not in CI pipeline!
    if test "$CI_RUNNER_VERSION" == 'unknown' -o "$CI_RUNNER_VERSION" == '' ; then
      mod_c='git config -f .gitmodules -l | awk '"'"'{split($0, a, /=/); split(a[1], b, /\./); print b[2], b[3], a[2]}'"'"
      modules=$(eval $mod_c | cut -d ' ' -f 1 | sort | uniq)
      for module in $modules ; do
        path=$(eval $mod_c | grep $module | grep path | rev | cut -d ' ' -f 1 | rev)
        branch=$(eval $mod_c | grep $module | grep branch | rev | cut -d ' ' -f 1 | rev)
        if test ! -z "$branch" ; then
          echo $path $branch
          set +x
          cd $path
          test 0 -eq $xtrace && set -o xtrace || true
          #git checkout $branch
          yellow Commit this submodule $module
          #_xtrace=$(shopt -o xtrace >/dev/null; echo $?)
          #set -x
          . $CICD_SHARED_DIR/scripts/tag_version.sh
          RC=$?
          #test 0 -ne $_xtrace && set +x
          test 0 -eq $RC || exit $RC
          set +x
          cd -
          test 0 -eq $xtrace && set -o xtrace || true
        else
          red ERROR: No branch for $module
          exit 1
        fi
      done
    fi
  fi

  test -z "$DISABLE_TAG_VERSION" && source $SHARED_CI_SCRIPTS_DIR/tag_version.sh || true
  RC=$? ; test 0 -eq $RC || exit $RC
fi

test 0 -eq $RC
