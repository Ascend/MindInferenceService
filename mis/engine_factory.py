# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
from os import path

from mis import constants
from mis.logger import init_logger
from mis.args import GlobalArgs

_LOCAL_LOGGING_INTERVAL_SEC = 5

logger = init_logger(__name__)


class AutoEngine:

    def __init__(self):
        pass

    @staticmethod
    def from_config(args: GlobalArgs):
        if args.engine_type == "vllm":
            logger.info("Using vllm backend")
            return VLLMEngine.from_args(args)
        elif args.engine_type == "mindie-service":
            logger.info("Using mindie-service backend")
            return MindIESvcEngine.from_args(args)
        elif args.engine_type == "tei-service":
            logger.info("Using tei-service backend")
            return TEISvcEngine.from_args(args)
        elif args.engine_type == "clip-service":
            logger.info("Using clip-service backend")
            return ClipSvcEngine.from_args(args)
        else:
            raise NotImplementedError(f"Model Engine for '{args.engine_type}' is not implemented,"
                                      f"available types are {constants.MIS_ENGINE_TYPES}.")


class VLLMEngine:

    def __init__(self):
        pass

    @staticmethod
    def from_args(args: GlobalArgs):
        from mis.llm.engines.vllm.engine import AsyncEngineArgs, AsyncLLMEngine

        if constants.MIS_VLM_ENABLE:
            engine_args = AsyncEngineArgs(model=args.model,
                                          served_model_name=args.served_model_name,
                                          disable_log_stats=args.disable_log_stats,
                                          disable_log_requests=args.disable_log_requests,
                                          allowed_local_media_path=args.allowed_local_media_path,
                                          limit_mm_per_prompt={
                                              "image": args.limit_image_per_prompt,
                                              "video": args.limit_video_per_prompt,
                                              "audio": args.limit_audio_per_prompt
                                          },
                                          **args.engine_optimization_config)
        else:
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

        if constants.MIS_VLM_ENABLE:
            return AsyncLLMEngine.from_engine_args(engine_args,
                                                   stat_loggers=stat_loggers)
        else:
            return AsyncLLMEngine.from_engine_args(engine_args,
                                                   engine_config=engine_config,
                                                   stat_loggers=stat_loggers)


class MindIESvcEngine:

    def __init__(self):
        pass

    @staticmethod
    def from_args(args: GlobalArgs):
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


class TEISvcEngine:

    def __init__(self):
        pass

    @staticmethod
    def from_args(args: GlobalArgs):
        from mis.emb.engines.tei.engine import TEIServiceEngine, TEIServiceArgs

        model_path = path.join(args.cache_path, args.model)

        tei_args = TEIServiceArgs(model_path, args.inner_port)

        return TEIServiceEngine(tei_args)


class ClipSvcEngine:
    def __init__(self):
        pass

    @staticmethod
    def from_args(args: GlobalArgs):
        from mis.emb.engines.clip.engine import ClipServiceArgs, ClipServiceEngine

        current_work_dir = os.path.dirname(__file__)
        config_path = path.join(current_work_dir, "config.yaml")
        clip_args = ClipServiceArgs(config_path, args.inner_port)

        return ClipServiceEngine(clip_args)
