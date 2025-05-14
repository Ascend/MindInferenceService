#!/bin/bash
# Copyright 2025 Huawei Technologies Co., Ltd.

set -e

workdir=$(
  cd $(dirname $0) || exit
  pwd
)

function compile_mis() {
  cd $workdir
  python3.10 setup.py bdist_wheel
  python3.11 setup.py bdist_wheel

  mkdir -p $workdir/output/mis
  rm -rf $workdir/output/mis/*
  # 输出whl包，模型配置config和量化补丁patch
  cp dist/* $workdir/output/mis/
  cp -r configs $workdir/output/mis/
  cp -r patch $workdir/output/mis/
}

function compile_mis_operator() {
  # pre build controller-gen
  cd $workdir/mis-operator
  go get sigs.k8s.io/controller-tools@v0.13.0
  GOMODCACHE=$(go env GOMODCACHE)
  cd $GOMODCACHE/sigs.k8s.io/controller-tools\@v0.13.0/
  CGO_ENABLED=0 GOOS=linux go build -a -o /opt/buildtools/controller-gen cmd/controller-gen/main.go

  # compile
  cd $workdir/mis-operator
  go mod tidy
  /opt/buildtools/controller-gen rbac:roleName=manager-role crd paths="./api/..." paths="./internal/..." output:crd:artifacts:config=config/crd/bases
  /opt/buildtools/controller-gen object:headerFile="hack/boilerplate.go.txt" paths="./api/..."
  CGO_ENABLED=0 GOOS=linux go build -a -o mis-operator-manager cmd/main.go

  # move
  mkdir -p $workdir/output/mis-operator
  rm -rf $workdir/output/mis-operator/*
  cp -r $workdir/mis-operator/config $workdir/output/mis-operator/
  cp -r $workdir/mis-operator/mis-operator-manager $workdir/output/mis-operator/
  cp -r $workdir/mis-operator/Dockerfile $workdir/output/mis-operator/
}

compile_mis
compile_mis_operator
