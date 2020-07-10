#!/usr/bin/env bash

. scripts/wheel-preamble.rc

# Clean up old things
rm -fr build || true

# The wheel config
cat - <<EOL >$LOCAL_BUILD_DIR/setup.py
from setuptools import setup, find_packages

setup(
      name='lambdacore-layer',
      version="$VERSION",
      packages=[],
      data_files = [('', ['$(basename $PACKAGE_ARTIFACT_FILE)'])],
      zip_safe=True,
      )
EOL

## Inspect
#pyenv version
#pip list

# Build the wheel
python setup.py clean bdist_wheel --python-tag py3 --universal --keep-temp --dist-dir $LOCAL_DIST_DIR

# Inspect
ls -al $LOCAL_DIST_DIR

cd $CI_PROJECT_DIR
