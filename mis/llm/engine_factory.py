# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from typing import Type

from mis import constants
from mis.args import GlobalArgs
from mis.logger import init_logger, LogType

logger = init_logger(__name__, log_type=LogType.SERVICE)


class AutoEngine:
    """A factory class that creates and returns LLM engine based on the provided config arguments."""
    def __init__(self):
        """Initialize the AutoEngine class. This constructor is currently not used."""
        pass

    @staticmethod
    def from_config(args: GlobalArgs) -> Type['AsyncLLMEngine']:
        """ Factory method to create an LLM engine instance based on the engine_type specified in the GlobalArgs.
        Args:
            args (GlobalArgs): A GlobalArgs instance containing the configuration for the LLM engine.
        Returns:
            Type['AsyncLLMEngine']: An instance of the selected LLM engine.
        Raises:
            NotImplementedError: If the specified engine_type is not supported.
        """
        if not args or not isinstance(args, GlobalArgs):
            logger.error(f"Invalid args type: {type(args)}, GlobalArgs needed")
            raise TypeError(f"Invalid args type: {type(args)}, GlobalArgs needed")
        if args.engine_type == "vllm":
            logger.info("Using vllm backend.")
            return VLLMEngine.from_args(args)
        else:
            logger.error(f"Model Engine for '{args.engine_type}' is not implemented, "
                         f"available types are {constants.MIS_ENGINE_TYPES}.")
            raise NotImplementedError(f"Model Engine for '{args.engine_type}' is not implemented, "
                                      f"available types are {constants.MIS_ENGINE_TYPES}.")


class VLLMEngine:
    """A class that build vLLM engine and provides a unified interface for initializing."""
    def __init__(self):
        """Initialize the VLLMEngine class. This constructor is currently not used."""
        pass

    @staticmethod
    def from_args(args: GlobalArgs) -> Type['AsyncLLMEngine']:
        """Factory method to create and initialize the vLLM engine using the provided GlobalArgs.
        Args:
            args (GlobalArgs): A GlobalArgs instance containing the configuration for the vLLM engine.
        Returns:
            Type['AsyncLLMEngine']: An initialized instance of the vLLM engine.
        Raises:
            ImportError: If the required modules for vLLM engine cannot be imported.
            Exception: If the vLLM engine fails to initialize for any reason.
        """
        if not args or not isinstance(args, GlobalArgs):
            logger.error(f"Invalid args type: {type(args)}, GlobalArgs needed")
            raise TypeError(f"Invalid args type: {type(args)}, GlobalArgs needed")
        try:
            from vllm.engine.arg_utils import AsyncEngineArgs
            from vllm.engine.async_llm_engine import AsyncLLMEngine
        except ImportError as e:
            logger.error(f"Failed to import required modules from vllm: {e}")
            raise ImportError(f"Failed to import required modules from vllm: {e}") from e
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
