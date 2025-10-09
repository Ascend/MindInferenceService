# -*- coding:utf-8 -*-
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
    host: Optional[str] = envs.MIS_HOST
    port: int = envs.MIS_PORT
    enable_dos_protection: bool = envs.MIS_ENABLE_DOS_PROTECTION
    ssl_keyfile: Optional[str] = envs.MIS_SSL_KEYFILE
    ssl_certfile: Optional[str] = envs.MIS_SSL_CERTFILE
    ssl_ca_certs: Optional[str] = envs.MIS_SSL_CA_CERT
    ssl_cert_reqs: int = envs.MIS_SSL_CERT_REQS
    log_level: str = envs.MIS_LOG_LEVEL
    max_log_len: Optional[int] = envs.MIS_MAX_LOG_LEN
    disable_log_requests: bool = constants.MIS_DISABLE_LOG_REQUESTS
    disable_log_stats: bool = constants.MIS_DISABLE_LOG_STATS

    uvicorn_log_level: str = envs.UVICORN_LOG_LEVEL

    # generated params
    engine_optimization_config: dict = {}


ARGS: GlobalArgs = GlobalArgs()
