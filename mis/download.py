# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.

from mis.args import ARGS
from mis.hub.envpreparation import environment_preparation
from mis.logger import init_logger

logger = init_logger(__name__)


def main():
    args = environment_preparation(ARGS, True)
    if not args.model:
        raise ValueError("MIS Downloader failed to find model name")
    logger.info(f"[MIS Downloader] [model] [{args.model.split('/')[-1]}]")


if __name__ == "__main__":
    main()
