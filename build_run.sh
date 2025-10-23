#!/bin/bash
# Copyright 2025 Huawei Technologies Co., Ltd.

set -e

workdir=$(
  cd $(dirname $0) || exit
  pwd
)

# 获取第一个入参，版本号
VERSION="${1:-7.0.0}"
ARCH=$(uname -m)
echo $VERSION

PROCESS_DIR=$workdir/output/process
TARGET_DIR=$workdir/output/target
mkdir -p $PROCESS_DIR
mkdir -p $TARGET_DIR

# 拷贝脚本至process目录
cp $workdir/output/Ascend-mis*.tar.gz $PROCESS_DIR
cp $workdir/output/uninstall.sh $PROCESS_DIR
cp $workdir/output/help.info $PROCESS_DIR
cp $workdir/output/install.sh $PROCESS_DIR

cp /usr1/opensource/makeself/makeself.sh $PROCESS_DIR
cp /usr1/opensource/makeself/makeself-header.sh $PROCESS_DIR
cp /usr1/mindxsdk/build/conf/scripts/eula_* $PROCESS_DIR

cd $PROCESS_DIR

# 设置文件权限
chmod 400 eula_*
chmod 500 *.sh
chmod 640 Ascend-mis*.tar.gz
chmod 440 help.info

bash makeself.sh --chown --nomd5 --sha256 --nocrc \
	--header makeself-header.sh \
	--help-header help.info \
	--packaging-date "" \
	--tar-extra '--owner=root --group=root' \
	$PROCESS_DIR \
	$TARGET_DIR/Ascend-mindsdk-mis_${VERSION}_linux-$ARCH.run \
	"ASCEND MIS RUN PACKAGE" \
  ./install.sh
