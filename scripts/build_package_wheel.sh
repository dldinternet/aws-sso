#!/usr/bin/env bash

. scripts/wheel-preamble.rc

# Prepare to make a wheel for our package
#cp $CI_PROJECT_DIR/setup.py $LOCAL_BUILD_DIR/python
#pip install -r $CI_PROJECT_DIR/requirements.txt >$LOCAL_BUILD_DIR/pip.requirements-whl.log
cd $LOCAL_BUILD_DIR/python
copper PWD: `pwd`

# All the packages that our package needs is here
export PYTHONPATH=$LOCAL_BUILD_DIR/python

# Set up the setuptools and wheel support
pip install --upgrade -r $CI_PROJECT_DIR/requirements-whl.txt >$LOCAL_BUILD_DIR/pip.requirements-whl.log
#python $CI_PROJECT_DIR/setup.py --help-commands 2>&1
test -z "$(python $CI_PROJECT_DIR/setup.py --help-commands 2>&1 | grep bdist_wheel)" && { red "bdist_wheel!?"; red "$(python $CI_PROJECT_DIR/setup.py --help-commands 2>&1 )"; python setup.py --help-commands 2>&1; exit 1; }
# Build the wheel
python $CI_PROJECT_DIR/setup.py clean bdist_wheel --python-tag py3 --universal --keep-temp --dist-dir $LOCAL_DIST_DIR

#set -x


cd $CI_PROJECT_DIR
