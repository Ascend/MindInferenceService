#!/bin/bash
# Copyright 2025 Huawei Technologies Co., Ltd.

set -e

workdir=$(
  cd $(dirname $0) || exit
  pwd
)

VERSION_FILE=$workdir/../mindxsdk/build/conf/config.yaml
ARCH=$(uname -m)
export CFLAGS="-fstack-protector-strong -fPIC -D_FORTIFY_SOURCE=2 -O2 -ftrapv"
export LDFLAGS="-Wl,-z,relro,-z,now,-z,noexecstack -s"

function get_version() {
  if [ -f "$VERSION_FILE" ]; then
    VERSION=$(sed '/.*mindxsdk:/!d;s/.*: //' "$VERSION_FILE")
    if [[ "$VERSION" == *.[b/B]* ]] && [[ "$VERSION" != *.[RC/rc]* ]]; then
      VERSION=${VERSION%.*}
    fi
  else
    VERSION="7.0.0"
  fi
}

get_version

function compile_mis() {
  echo "compile mis"

  cd $workdir
  mkdir -p $workdir/output/mis
  rm -rf $workdir/output/mis/*
  mkdir $workdir/output/mis/llm

  echo "Mind Inference Service: ${VERSION}" >> $workdir/output/mis/version.info

  # 编译tei需要的whl包
  python3.11 setup.py bdist_wheel
  mv dist/* $workdir/output/mis/

  python3.10 setup.py bdist_wheel
  mv dist/* $workdir/output/mis/llm

  # 输出模型配置config和量化补丁patch
  cp -r configs $workdir/output/mis/
  cp -r patch $workdir/output/mis/
}

function compile_mis_operator() {
  echo "compile mis operator"

  OUTPUT_NAME=mis-operator-manager

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

  export CGO_ENABLED=0

  go build \
  -buildmode=pie \
  -trimpath \
  -ldflags "-s -linkmode=external -extldflags=-Wl,-z,relro,-z,now,-z,noexecstack -X main.BuildName=${OUTPUT_NAME} -X main.BuildVersion=${VERSION}_linux-${ARCH}" \
  -o ${OUTPUT_NAME} cmd/main.go

  # move
  mkdir -p $workdir/output/mis-operator
  rm -rf $workdir/output/mis-operator/*

  echo "MIS Operator: ${VERSION}" >> $workdir/output/mis-operator/version.info

  cp -r $workdir/mis-operator/config $workdir/output/mis-operator/
  cp -r $workdir/mis-operator/mis-operator-manager $workdir/output/mis-operator/
  cp -r $workdir/mis-operator/Dockerfile $workdir/output/mis-operator/
}

function package() {
  package_dir=$1
  target_name=$2

  cd $workdir/output/$package_dir

  #将所有目录设置为750，特殊目录单独处理
  find ./ -type d -exec chmod 750 {} \;
  #将所有文件设置640，特殊文件单独处理
  find ./ -type f -exec chmod 640 {} \;
  #将所有的sh和run文件设置为550
  find ./  \( -name "*.sh" -o -name "*.run" \)  -exec  chmod 550 {} \;

  cd ..

  tar -zcvf $target_name $package_dir

  rm -rf $package_dir
}

compile_mis
package mis $workdir/output/Ascend-mis_"$VERSION"_linux-"$ARCH".tar.gz

compile_mis_operator
package mis-operator $workdir/output/Ascend-mis-operator_"$VERSION"_linux-"$ARCH".tar.gz
