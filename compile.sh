#!/bin/bash
# Copyright 2025 Huawei Technologies Co., Ltd.
# Author: Mind Inference Service
# Create: 2025
# History: NA

set -e

workdir=$(
  cd "$(dirname "$0")" || exit
  pwd
)

VERSION_FILE="$workdir/../mindxsdk/build/conf/config.yaml"
ARCH=$(uname -m)

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
  echo "build mis"

  cd "$workdir"
  mkdir -p "$workdir/output/mis"
  rm -rf "$workdir/output/mis/*"

  echo "Mind Inference Service: ${VERSION}" >> "$workdir/output/mis/version.info"

  # Package pyz packages for MIS
  python3 build.py
  cp -r dist/* "$workdir/output/mis/"

  cp -r configs "$workdir/output/mis/"

  cp script/run/* "$workdir/output"
}

function package() {
  package_dir=$1
  target_name=$2
  echo "package mis"
  cd "$workdir/output/$package_dir"

  # Set all directories to 750, and handle special directories separately.
  find ./ -type d -exec chmod 750 {} \;
  # Set all files to 640 permissions, and handle special files separately.
  find ./ -type f -exec chmod 640 {} \;
  # Set all pyz files to 550.
  find ./ -name "*.pyz" -exec chmod 550 {} \;
  find ./ -name "version.info" -exec chmod 440 {} \;

  cd ..
  find ./ -type f -path "*.sh" -exec chmod 500 {} \;
  tar -zcvf "$target_name" -C "$package_dir" .

  rm -rf "$package_dir"
}

compile_mis
package mis "$workdir/output/Ascend-mis_${VERSION}_linux-$ARCH.tar.gz"
