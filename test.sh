#!/bin/bash
# Copyright 2025 Huawei Technologies Co., Ltd.
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

  if ! (python3.11 -m pytest --junit-xml=final.xml --html=./final.html --self-contained-html --durations=5 -vs --cov-branch --cov=./ --cov-report=html --cov-report=xml:coverage.xml .); then
    echo "*********mis Python test cases error*********"
    exit 1
  else
    echo "*********mis Python test cases success*********"
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