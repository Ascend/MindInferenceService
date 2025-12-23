#!/usr/bin/env python
# coding=utf-8
"""
-------------------------------------------------------------------------
This file is part of the Mind Inference Service project.
Copyright (c) 2025 Huawei Technologies Co.,Ltd.

Mind Inference Service is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:

         http://license.coscl.org.cn/MulanPSL2

THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
See the Mulan PSL v2 for more details.
-------------------------------------------------------------------------
"""
import os

import mis.constants as constants
from mis.args import GlobalArgs
from mis.llm.engines.config_parser import ConfigParser
from mis.logger import init_logger, LogType
from mis.utils.utils import get_model_path

logger = init_logger(__name__, log_type=LogType.SERVICE)


def _source_components_envs() -> None:
    """Set the environment variables of the third-party component to the fixed value."""
    for components_env in constants.OFFLINE_COMPONENTS_ENVS:
        os.environ[components_env] = "1"
        logger.info(f"Set environment variable {components_env} to 1")
    for components_key, components_value in constants.SOURCE_COMPONENTS_ENVS.items():
        os.environ[components_key] = components_value
        logger.info(f"Set environment variable {components_key} to {components_value}")


def environment_preparation(args: GlobalArgs) -> GlobalArgs:
    """Do some preparations for mis
        include:
            - model-preferred-config-resolve
            - set environment variables if needed
    """
    logger.info("Starting environment preparation")
    if not args or not isinstance(args, GlobalArgs):
        logger.error(f"Invalid args type: {type(args)}, GlobalArgs needed")
        raise TypeError(f"Invalid args type: {type(args)}, GlobalArgs needed")

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
    logger.debug("Resolved model path")

    logger.info("Environment preparation completed")
    return args
