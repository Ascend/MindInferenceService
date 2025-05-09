# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import ssl

MIS_ENGINE_TYPES = ["vllm", "mindie-service"]

MIS_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

UVICORN_LOG_LEVELS = ["debug", "info", "warning", "error", "critical"]

SSL_CERT_REQS_TYPES = [int(ssl.CERT_NONE), int(ssl.CERT_OPTIONAL), int(ssl.CERT_REQUIRED)]

ASCEND_PATH = "/usr/local/Ascend"

ASCEND_TOOLKIT_PATH = f"{ASCEND_PATH}/ascend-toolkit/latest"

ASCEND_NNAL_PATH = f"{ASCEND_PATH}/nnal/atb"

MINDIE_PATH = f"{ASCEND_PATH}/mindie/latest"
MINDIE_RT_PATH = F"{MINDIE_PATH}/mindie-rt"
MINDIE_TORCH_PATH = F"{MINDIE_PATH}/mindie-torch"
MINDIE_SERVICE_PATH = f"{MINDIE_PATH}/mindie-service"
MINDIE_SERVICE_CONFIG_PATH = f"{MINDIE_SERVICE_PATH}/conf/config.json"
MINDIE_LLM_PATH = f"{MINDIE_PATH}/mindie-llm"

MINDIE_ATB_PATH = f"{ASCEND_PATH}/atb"
