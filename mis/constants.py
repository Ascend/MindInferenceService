# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import ssl

MIS_ENGINE_TYPES = ["vllm"]

MIS_SERVICE_TYPES = ["openai"]

MIS_OPTIMIZATION_CONFIG_TYPES = ["default", "throughput", "latency"]

MIS_LOG_LEVELS = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

UVICORN_LOG_LEVELS = ["debug", "info", "warning", "error", "critical"]

SSL_CERT_REQS_TYPES = [ssl.CERT_NONE, ssl.CERT_OPTIONAL, ssl.CERT_REQUIRED]
