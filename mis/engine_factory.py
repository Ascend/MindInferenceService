# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from vllm.engine.protocol import EngineClient

from mis import constants
from mis.logger import init_logger
from mis.args import GlobalArgs

_LOCAL_LOGGING_INTERVAL_SEC = 5

logger = init_logger(__name__)


class AutoEngine:

    @staticmethod
    def from_config(args: GlobalArgs) -> EngineClient:
        if args.engine_type == "vllm":
            logger.info("Using vllm backend")
            return VLLMEngine.from_args(args)
        elif args.engine_type == "mindie-service":
            logger.info("Using mindie-service backend")
            return MindIESvcEngine.from_args(args)
        else:
            raise NotImplementedError(f"Model Engine for '{args.engine_type}' is not implemented,"
                                      f"available types are {constants.MIS_ENGINE_TYPES}.")


class VLLMEngine:

    @staticmethod
    def from_args(args: GlobalArgs) -> EngineClient:
        from mis.llm.engines.vllm.engine import AsyncEngineArgs, AsyncLLMEngine

        engine_args = AsyncEngineArgs(model=args.model,
                                      served_model_name=args.served_model_name,
                                      disable_log_stats=args.disable_log_stats,
                                      disable_log_requests=args.disable_log_requests,
                                      **args.engine_optimization_config)
        engine_config = engine_args.create_engine_config()

        from vllm.engine.metrics import LoggingStatLogger
        from mis.llm.engines.vllm.metrics import MisPrometheusStatLogger

        stat_loggers = None
        if not args.disable_log_stats:
            stat_loggers = {
                "logging": LoggingStatLogger(
                    local_interval=_LOCAL_LOGGING_INTERVAL_SEC,
                    vllm_config=engine_config
                ),
                "prometheus": MisPrometheusStatLogger(
                    local_interval=_LOCAL_LOGGING_INTERVAL_SEC,
                    labels=dict(model_name=engine_config.model_config.served_model_name),
                    vllm_config=engine_config
                ),
            }

        return AsyncLLMEngine.from_engine_args(engine_args,
                                               engine_config=engine_config,
                                               stat_loggers=stat_loggers)


class MindIESvcEngine:

    @staticmethod
    def from_args(args: GlobalArgs) -> EngineClient:
        from mis.llm.engines.vllm.engine import AsyncEngineArgs
        from mis.llm.engines.mindie.engine import MindIEServiceEngine, MindIEServiceArgs

        engine_args = AsyncEngineArgs(model=args.model,
                                      served_model_name=args.served_model_name,
                                      disable_log_stats=args.disable_log_stats,
                                      disable_log_requests=args.disable_log_requests,
                                      **args.engine_optimization_config)
        engine_config = engine_args.create_engine_config()

        mindie_args = MindIEServiceArgs(engine_config, args.host or "0.0.0.0")
        return MindIEServiceEngine(mindie_args)
