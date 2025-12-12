#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import stat


MIS_MODEL_LIST = ("Qwen3-8B", )

MIS_ENGINE_TYPES = ("vllm", "triton")

MIS_CONFIGS_LIST = ("atlas800ia2-1x32gb-bf16-vllm-default",
                    "atlas800ia2-1x32gb-bf16-vllm-latency",
                    "atlas800ia2-1x32gb-bf16-vllm-throughput"
                    )

MIS_HOST = "127.0.0.1"

MIS_MAX_CONFIG_SIZE = 1024 * 1024

MIS_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

MIS_DISABLE_LOG_REQUESTS = True

MIS_DISABLE_LOG_STATS = True

UVICORN_LOG_LEVELS = ("debug", "info", "warning", "error", "critical")

HW_910B = "910B"

OFFLINE_COMPONENTS_ENVS = ("VLLM_DO_NOT_TRACK", "HF_DATASETS_OFFLINE", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
SOURCE_COMPONENTS_ENVS = {"VLLM_HOST_IP": "127.0.0.1", "GLOO_SOCKET_IFNAME": "lo"}

MAX_REQUEST_HEADER_SIZE = 8192  # 8KB
MAX_REQUEST_BODY_SIZE = 50 * 1024 * 1024
MAX_CONCURRENT_REQUESTS = 512
RATE_LIMIT_PER_MINUTE = 60
REQUEST_TIMEOUT_IN_SEC = 2500

DIRECTORY_PERMISSIONS = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP  # 750
FILE_PERMISSIONS = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP  # 640
ARCHIVED_FILE_PERMISSIONS = stat.S_IRUSR | stat.S_IRGRP  # 440
