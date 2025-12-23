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

set -e

workdir=$(
  cd "$(dirname "$0")" || exit
  pwd
)

# 获取第一个入参，版本号
VERSION="${1:-7.0.0}"
ARCH=$(uname -m)
echo "$VERSION"

PROCESS_DIR="$workdir/output/process"
TARGET_DIR="$workdir/output/target"
mkdir -p "$PROCESS_DIR"
mkdir -p "$TARGET_DIR"

# 拷贝脚本至process目录
cp "$workdir/output/"Ascend-mis*.tar.gz "$PROCESS_DIR"
cp "$workdir/output/uninstall.sh" "$PROCESS_DIR"
cp "$workdir/output/help.info" "$PROCESS_DIR"
cp "$workdir/output/install.sh" "$PROCESS_DIR"

cd "$PROCESS_DIR"

# 设置文件权限
chmod 500 -- *.sh
chmod 640 Ascend-mis*.tar.gz
chmod 440 help.info

bash $workdir/opensource/makeself/makeself.sh --chown --nomd5 --sha256 --nocrc \
    --header $workdir/opensource/makeself/makeself-header.sh \
    --help-header help.info \
    --packaging-date "" \
    --tar-extra '--owner=root --group=root' \
    "$PROCESS_DIR" \
    "$TARGET_DIR/Ascend-mis_${VERSION}_linux-$ARCH.run" \
    "ASCEND MIS RUN PACKAGE" \
  ./install.sh