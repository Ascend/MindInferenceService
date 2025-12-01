#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from typing import Optional

from pydantic import BaseModel

import mis.envs as envs
from mis import constants


class GlobalArgs(BaseModel):
    # environment params
    cache_path: str = envs.MIS_CACHE_PATH
    model: str = envs.MIS_MODEL
    engine_type: str = envs.MIS_ENGINE_TYPE
    served_model_name: Optional[str] = None
    mis_config: str = envs.MIS_CONFIG

    # server
    host: str = constants.MIS_HOST
    port: int = envs.MIS_PORT
    enable_dos_protection: bool = envs.MIS_ENABLE_DOS_PROTECTION
    log_level: str = envs.MIS_LOG_LEVEL
    max_log_len: int = constants.MIS_MAX_LOG_LEN
    disable_log_requests: bool = constants.MIS_DISABLE_LOG_REQUESTS
    disable_log_stats: bool = constants.MIS_DISABLE_LOG_STATS

    # generated params
    engine_optimization_config: dict = {}


ARGS: GlobalArgs = GlobalArgs()
