# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from typing import Type

from mis import constants
from mis.args import GlobalArgs
from mis.logger import init_logger

logger = init_logger(__name__)


class AutoEngine:

    def __init__(self):
        pass

    @staticmethod
    def from_config(args: GlobalArgs) -> Type['AsyncLLMEngine']:
        if args.engine_type == "vllm":
            logger.info("Using vllm backend.")
            return VLLMEngine.from_args(args)
        else:
            logger.error(f"Model Engine for '{args.engine_type}' is not implemented."
                         f"available types are {constants.MIS_ENGINE_TYPES}.")
            raise NotImplementedError(f"Model Engine for '{args.engine_type}' is not implemented,"
                                      f"available types are {constants.MIS_ENGINE_TYPES}.")


class VLLMEngine:

    def __init__(self):
        pass

    @staticmethod
    def from_args(args: GlobalArgs) -> Type['AsyncLLMEngine']:
        try:
            from vllm.engine.arg_utils import AsyncEngineArgs
            from vllm.engine.async_llm_engine import AsyncLLMEngine
        except ImportError as e:
            logger.error(f"Failed to import AsyncLLMEngine: {e}")
            raise ImportError(f"Failed to import AsyncLLMEngine: {e}") from e
        try:
            engine_args = AsyncEngineArgs(model=args.model,
                                          served_model_name=args.served_model_name,
                                          disable_log_stats=args.disable_log_stats,
                                          disable_log_requests=args.disable_log_requests,
                                          **args.engine_optimization_config)
            logger.info(f"AsyncLLMEngine args initialized successfully.")
            return AsyncLLMEngine.from_engine_args(engine_args)
        except Exception as e:
            logger.error(f"Failed to initialize AsyncLLMEngine: {e}")
            raise Exception(f"Failed to initialize AsyncLLMEngine: {e}") from e
