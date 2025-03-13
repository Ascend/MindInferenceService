# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from mis.logger import init_logger
from mis.args import GlobalArgs
from mis.hub.downloader import ModelerDownloader
from mis.llm.engines.config import ConfigParser

logger = init_logger(__name__)


def environment_preparation(args: GlobalArgs) -> GlobalArgs:
    """Do some preparations for mis
        include:
            - model-pre-downloading
            - model-preferred-config-resolve
    """
    if args.served_model_name is None:
        args.served_model_name = args.model

    # download model
    args.model = ModelerDownloader.get_model_path(args.model)

    # preferred config
    configparser = ConfigParser(args)
    args = configparser.engine_config_loading()

    return args
