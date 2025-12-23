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
    max_log_len: Optional[int] = envs.MIS_MAX_LOG_LEN
    disable_log_requests: bool = constants.MIS_DISABLE_LOG_REQUESTS
    disable_log_stats: bool = constants.MIS_DISABLE_LOG_STATS

    uvicorn_log_level: str = envs.UVICORN_LOG_LEVEL

    # generated params
    engine_optimization_config: dict = {}


ARGS: GlobalArgs = GlobalArgs()
