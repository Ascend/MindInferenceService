#!/bin/bash
# -------------------------------------------------------------------------
# This file is part of the Mind Inference Service project.
# Copyright (c) 2025 Huawei Technologies Co.,Ltd.
#
# Mind Inference Service is licensed under Mulan PSL v2.
# You can use this software according to the terms and conditions of the Mulan PSL v2.
# You may obtain a copy of Mulan PSL v2 at:
#
#          http://license.coscl.org.cn/MulanPSL2
#
# THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
# EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
# MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
# See the Mulan PSL v2 for more details.
# -------------------------------------------------------------------------
# Author: Mind Inference Service
# Create: 2025
# History: NA

set -e

workdir=$(
  cd $(dirname $0) || exit
  pwd
)

PY_EXE=python3.11

function set_pythonpath() {
  SITE_DIRS=$($PY_EXE -c "import site; print(site.getsitepackages())")
  SITE_DIR=$(echo $SITE_DIRS | tr -d '[]' | tr -d \")

  export PYTHONPATH="${SITE_DIR}${PYTHONPATH:+:$PYTHONPATH}"

  echo "PYTHONPATH setting to: "
  echo "$PYTHONPATH"
}

function test_mis() {
  # prepare test
  cd $workdir/mis

    # Define the list of dependencies as an array
  dependencies=(
    "pytest"
    "pytest-cov"
    "pytest-html"
    "starlette"
    "vllm==0.9.1"
    "uvicorn"
    "cryptography"
    "transformers==4.52.3"
  )

  # Install each dependency individually
  for dep in "${dependencies[@]}"; do
    echo "Installing: $dep"
    python3.11 -m pip install "$dep"
  done

  # Add the mis module to the Python path
  export PYTHONPATH=$workdir:$PYTHONPATH

  mis_cache_path=$(python3.11 -c "import os; print(os.environ.get('MIS_CACHE_PATH'))")

  if [ -z "$mis_cache_path" ]; then
    mis_cache_path=$(python3.11 -c "import os; print(os.path.join(os.path.expanduser('~'), 'mis', '.cache'))")
    echo "MIS_CACHE_PATH is not set. Using default path: $mis_cache_path"
  fi

  if [ ! -d "$mis_cache_path" ]; then
    echo "MIS_CACHE_PATH directory does not exist: $mis_cache_path"
  else
    original_perms=$(stat -c "%a" "$mis_cache_path")
    echo "Original permissions of $mis_cache_path: $original_perms"

    chmod 750 "$mis_cache_path"
    echo "Changed permissions of $mis_cache_path to 750"
  fi

  if ! (python3.11 -m pytest --junit-xml=final.xml --html=./final.html --self-contained-html --durations=5 -vs --cov-branch --cov=./ --cov-report=html --cov-report=xml:coverage.xml .); then
    echo "*********mis Python test cases error*********"
    exit 1
  else
    echo "*********mis Python test cases success*********"
  fi

  if [ -n "$mis_cache_path" ] && [ -d "$mis_cache_path" ]; then
    echo "Restoring permissions of $mis_cache_path to $original_perms"
    chmod "$original_perms" "$mis_cache_path"
  fi

  # move
  mkdir -p $workdir/coverage/mis
  rm -rf $workdir/coverage/mis/*

  cp -r htmlcov $workdir/coverage/mis
  cp final.html $workdir/coverage/mis
  cp final.xml $workdir/coverage/mis
  cp coverage.xml $workdir/coverage/mis
  cp .coverage $workdir/coverage/mis
  rm final.html final.xml coverage.xml .coverage
  rm -rf htmlcov
}

set_pythonpath
test_mis