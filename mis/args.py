# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from typing import Optional, Any, ClassVar

from pydantic import BaseModel

import mis.envs as envs

TOOL_PARSER_TYPE = "pythonic"


class GlobalArgs(BaseModel):
    model_post_init: ClassVar[Any]

    # environment params
    cache_path: str = envs.MIS_CACHE_PATH

    model: str = envs.MIS_MODEL
    engine_type: str = envs.MIS_ENGINE_TYPE
    served_model_name: Optional[str] = envs.MIS_SERVED_MODEL_NAME
    max_model_len: Optional[int] = envs.MIS_MAX_MODEL_LEN
    enable_prefix_caching: bool = envs.MIS_ENABLE_KV_CACHE_REUSE
    mis_config: str = envs.MIS_CONFIG
    trust_remote_code: bool = envs.MIS_TRUST_REMOTE_CODE

    # server
    host: Optional[str] = envs.MIS_HOST
    port: int = envs.MIS_PORT
    metrics_port: int = envs.MIS_METRICS_PORT
    inner_port: int = envs.MIS_INNER_PORT
    ssl_keyfile: Optional[str] = envs.MIS_SSL_KEYFILE
    ssl_certfile: Optional[str] = envs.MIS_SSL_CERTFILE
    ssl_ca_certs: Optional[str] = envs.MIS_SSL_CA_CERT
    ssl_cert_reqs: int = envs.MIS_SSL_CERT_REQS
    log_level: str = envs.MIS_LOG_LEVEL
    max_log_len: Optional[int] = envs.MIS_MAX_LOG_LEN
    disable_log_requests: bool = envs.MIS_DISABLE_LOG_REQUESTS
    disable_log_stats: bool = envs.MIS_DISABLE_LOG_STATS
    disable_fastapi_docs: bool = envs.MIS_DISABLE_FASTAPI_DOCS

    # vlm params
    allowed_local_media_path: str = envs.MIS_ALLOWED_LOCAL_MEDIA_PATH
    limit_image_per_prompt: int = envs.MIS_LIMIT_IMAGE_PER_PROMPT
    limit_video_per_prompt: int = envs.MIS_LIMIT_VIDEO_PER_PROMPT
    limit_audio_per_prompt: int = envs.MIS_LIMIT_AUDIO_PER_PROMPT

    uvicorn_log_level: str = envs.UVICORN_LOG_LEVEL

    # generated params
    engine_optimization_config: dict = {}

    enable_auto_tools: Optional[bool] = envs.MIS_ENABLE_AUTO_TOOLS
    tool_parser: Optional[str] = TOOL_PARSER_TYPE

    def model_post_init(self, __context: Any) -> None:
        """This method is called after the model has been fully initialized and validates configuration of MIS.

        Args:
            __context (Any): The context passed to the model during initialization. This is typically used for advanced
                use cases and is not used in this method.

        Raises:
            ValueError: If `port` and `metrics_port` are the same.
        """

        if self.port == self.metrics_port:
            raise ValueError("MIS_PORT and MIS_METRICS_PORT is not allowed to use the same port.")


ARGS: GlobalArgs = GlobalArgs()
