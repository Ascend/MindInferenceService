#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os

import mis.constants as constants
from mis.args import GlobalArgs
from mis.llm.engines.config_parser import ConfigParser
from mis.logger import init_logger, LogType
from mis.utils.utils import get_model_path

logger = init_logger(__name__, log_type=LogType.SERVICE)


def _source_components_envs() -> None:
    for components_env in constants.SOURCE_COMPONENTS_ENVS:
        if components_env not in os.environ:
            os.environ[components_env] = "1"
            logger.debug(f"Set environment variable {components_env} to 1")


def environment_preparation(args: GlobalArgs) -> GlobalArgs:
    """Do some preparations for mis
        include:
            - model-preferred-config-resolve
            - set environment variables if needed
    """
    logger.info("Starting environment preparation")

    _source_components_envs()
    logger.info("Loaded component environment variables")

    # preferred config
    configparser = ConfigParser(args)
    args = configparser.engine_config_loading()
    logger.debug("Loaded engine configuration")

    if args.served_model_name is None:
        args.served_model_name = args.model
        logger.info(f"Set served_model_name to {args.model}")

    args.model = get_model_path(args.model)
    logger.debug(f"Resolved model path")

    logger.info("Environment preparation completed")
    return args
