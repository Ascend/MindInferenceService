# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import ssl


def _is_root() -> bool:
    """Check if current user is root."""
    return os.getuid() == 0


def _get_base_path() -> str:
    """Return base path based on user privilege."""
    if _is_root():
        return "/usr/local"
    else:
        return "/home/HwHiAiUser"  # Fixed non-root username in the inference microservice


def _get_ascend_path() -> str:
    """Get the installation path of the Ascend series."""
    return os.path.join(_get_base_path(), "Ascend")


def _get_bin_path() -> str:
    """Get the local bin path."""
    if _is_root():
        return _get_base_path()  # root：/usr/local
    else:
        return os.path.join(_get_base_path(), ".local")  # non-root：$HOME/.local


MIS_MODEL_LIST = ("MindSDK/Qwen3-8B", )

MIS_ENGINE_TYPES = ("vllm",)

MIS_CONFIGS_LIST = ("atlas800ia2-1x32gb-bf16-vllm-default",
                    "atlas800ia2-1x32gb-bf16-vllm-latency",
                    "atlas800ia2-1x32gb-bf16-vllm-throughput"
                    )

MIS_MAX_CONFIG_SIZE = 1024 * 1024

MIS_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

MIS_LOCAL_BIN_PATH = _get_bin_path()

MIS_DISABLE_LOG_REQUESTS = True

MIS_DISABLE_LOG_STATS = True

UVICORN_LOG_LEVELS = ("debug", "info", "warning", "error", "critical")

SSL_CERT_REQS_TYPES = (int(ssl.CERT_NONE), int(ssl.CERT_OPTIONAL), int(ssl.CERT_REQUIRED))

MIS_SSL_CIPHERS = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"

ASCEND_PATH = _get_ascend_path()

ASCEND_TOOLKIT_PATH = f"{ASCEND_PATH}/ascend-toolkit/latest"

ASCEND_NNAL_PATH = f"{ASCEND_PATH}/nnal/atb"

HW_910B = "910B"

IP_ALL_ZERO = "0.0.0.0"

SOURCE_COMPONENTS_ENVS = ("VLLM_DO_NOT_TRACK", "HF_DATASETS_OFFLINE", "HF_HUB_OFFLINE")

MAX_REQUEST_BODY_SIZE = 50 * 1024 * 1024
MAX_CONCURRENT_REQUESTS = 512
RATE_LIMIT_PER_MINUTE = 60
REQUEST_TIMEOUT_IN_SEC = 2500
