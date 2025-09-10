# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import ssl


def is_root():
    """Check if current user is root."""
    return os.getuid() == 0


def get_base_path():
    """Return base path based on user privilege."""
    if is_root():
        return "/usr/local"
    else:
        return "/home/HwHiAiUser"  # Fixed non-root username in the inference microservice


def get_ascend_path():
    """Get the installation path of the Ascend series."""
    return os.path.join(get_base_path(), "Ascend")


def get_bin_path():
    """Get the local bin path."""
    if is_root():
        return get_base_path()  # root：/usr/local
    else:
        return os.path.join(get_base_path(), ".local")  # non-root：$HOME/.local


MIS_ENGINE_TYPES = ["vllm", "mindie-service", "tei-service", "clip-service"]

MIS_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

MIS_BASE_PATH = get_base_path()

MIS_LOCAL_BIN_PATH = get_bin_path()

UVICORN_LOG_LEVELS = ["debug", "info", "warning", "error", "critical"]

CONFIG2ENV_NAME_LIST = ["npu_memory_fraction", "vllm_allow_long_max_model_len", "vllm_use_v1"]

SSL_CERT_REQS_TYPES = [int(ssl.CERT_NONE), int(ssl.CERT_OPTIONAL), int(ssl.CERT_REQUIRED)]

ASCEND_PATH = get_ascend_path()

ASCEND_TOOLKIT_PATH = f"{ASCEND_PATH}/ascend-toolkit/latest"

ASCEND_NNAL_PATH = f"{ASCEND_PATH}/nnal/atb"

MINDIE_PATH = f"{ASCEND_PATH}/mindie/latest"
MINDIE_RT_PATH = F"{MINDIE_PATH}/mindie-rt"
MINDIE_TORCH_PATH = F"{MINDIE_PATH}/mindie-torch"
MINDIE_SERVICE_PATH = f"{MINDIE_PATH}/mindie-service"
MINDIE_SERVICE_CONFIG_PATH = f"{MINDIE_SERVICE_PATH}/conf/config.json"
MINDIE_LLM_PATH = f"{MINDIE_PATH}/mindie-llm"

MINDIE_ATB_PATH = f"{ASCEND_PATH}/atb"

HW_310P = "310P"
HW_910B = "910B"
