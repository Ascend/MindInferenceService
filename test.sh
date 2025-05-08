#!/bin/bash
# Copyright 2025 Huawei Technologies Co., Ltd.

set -e

workdir=$(
  cd $(dirname $0) || exit
  pwd
)

function test_mis_operator() {
  # prepare test
  cd $workdir/mis-operator
  go mod tidy

  # do test
  readonly FILE_TEST_RESULT='testMISOperator.txt'
  readonly FILE_DETAIL_OUTPUT='api.html'

  if ! (go test $(go list ./internal/...) -v -race -coverprofile=cover.out > ./$FILE_TEST_RESULT); then
    echo "*********mis-operator go test cases error*********"
    cat ./$FILE_TEST_RESULT
    exit 1
  else
    echo $FILE_DETAIL_OUTPUT
    gocov convert cover.out > gocov.json
    gocov convert cover.out | gocov-html > $FILE_DETAIL_OUTPUT
    gotestsum --junitfile unit-tests.xml ./...
  fi

  # move
  mkdir -p $workdir/coverage/mis-operator
  rm -rf $workdir/coverage/mis-operator/*

  cp $FILE_DETAIL_OUTPUT $workdir/coverage/mis-operator/
  cp gocov.json $workdir/coverage/mis-operator/
  cp unit-tests.xml $workdir/coverage/mis-operator/
}

test_mis_operator
