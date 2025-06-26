# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import ssl
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from mis.utils.env_checker import EnvChecker
import mis.constants as constants

if TYPE_CHECKING:
    MIS_CACHE_PATH: str = "/opt/mis/.cache"

    MIS_MODEL: str = "DeepSeek-R1-Distill-Qwen-7B"
    MIS_ENGINE_TYPE: str = "vllm"
    MIS_SERVED_MODEL_NAME: Optional[str] = None
    MIS_MAX_MODEL_LEN: Optional[int] = None
    MIS_ENABLE_KV_CACHE_REUSE: bool = False
    MIS_CONFIG: str = "atlas800ia2-32gb-bf16-vllm-default"
    MIS_TRUST_REMOTE_CODE: bool = False

    MIS_ENABLE_AUTO_TOOLS: bool = True

    MIS_HOST: Optional[str] = None
    MIS_PORT: int = 8000
    MIS_INNER_PORT = 9090
    MIS_SSL_KEYFILE: Optional[str] = None
    MIS_SSL_CERTFILE: Optional[str] = None
    MIS_SSL_CA_CERT: Optional[str] = None
    MIS_SSL_CERT_REQS: int = ssl.CERT_NONE
    MIS_FORCE_DOWNLOAD_MODEL: bool = False
    MIS_LOG_LEVEL: str = "INFO"
    MIS_MAX_LOG_LEN: Optional[int] = None
    MIS_DISABLE_LOG_REQUESTS: bool = False
    MIS_DISABLE_LOG_STATS: bool = False
    MIS_API_KEY: Optional[str] = None
    MIS_DISABLE_FASTAPI_DOCS: bool = False

    MIS_ALLOWED_LOCAL_MEDIA_PATH: str = "/opt"
    MIS_LIMIT_IMAGE_PER_PROMPT: int = 1
    MIS_LIMIT_VIDEO_PER_PROMPT: int = 1
    MIS_LIMIT_AUDIO_PER_PROMPT: int = 0

    UVICORN_LOG_LEVEL: str = "info"

environment_variables: Dict[str, Callable[[], Any]] = {
    "MIS_CACHE_PATH": lambda: _get_cache_path_from_env("MIS_CACHE_PATH", "/opt/mis/.cache"),
    "MIS_MODEL": lambda: _get_str_from_env("MIS_MODEL", "DeepSeek-R1-Distill-Qwen-7B"),
    "MIS_ENGINE_TYPE": lambda: _get_str_from_env("MIS_ENGINE_TYPE", "vllm", constants.MIS_ENGINE_TYPES),
    "MIS_SERVED_MODEL_NAME": lambda: _get_str_from_env("MIS_SERVED_MODEL_NAME", None),
    "MIS_MAX_MODEL_LEN": lambda: _get_int_from_env("MIS_MAX_MODEL_LEN", None),
    "MIS_ENABLE_KV_CACHE_REUSE": lambda: _get_bool_from_env("MIS_ENABLE_KV_CACHE_REUSE", False),
    "MIS_CONFIG": lambda: _get_optimization_config(),
    "MIS_TRUST_REMOTE_CODE": lambda: False,

    "MIS_ENABLE_AUTO_TOOLS": lambda: _get_bool_from_env("MIS_ENABLE_AUTO_TOOLS", True),

    "MIS_HOST": lambda: _get_ip_address_from_env("MIS_HOST", None),
    "MIS_PORT": lambda: _get_int_from_env("MIS_PORT", 8000, 1024, 65535),
    "MIS_INNER_PORT": lambda: _get_int_from_env("MIS_INNER_PORT", 9090, 1024, 65535),
    "MIS_SSL_KEYFILE": lambda: _get_file_from_env("MIS_SSL_KEYFILE", None),
    "MIS_SSL_CERTFILE": lambda: _get_file_from_env("MIS_SSL_CERTFILE", None),
    "MIS_SSL_CA_CERT": lambda: _get_file_from_env("MIS_SSL_CA_CERT", None),
    "MIS_SSL_CERT_REQS": lambda: _get_ssl_cert_reqs(),
    "MIS_FORCE_DOWNLOAD_MODEL": lambda: _get_bool_from_env("MIS_FORCE_DOWNLOAD_MODEL", False),
    "MIS_LOG_LEVEL": lambda: _get_str_from_env("MIS_LOG_LEVEL", "INFO", constants.MIS_LOG_LEVELS),
    "MIS_MAX_LOG_LEN": lambda: _get_int_from_env("MIS_MAX_LOG_LEN", None),
    "MIS_DISABLE_LOG_REQUESTS": lambda: _get_bool_from_env("MIS_DISABLE_LOG_REQUESTS", False),
    "MIS_DISABLE_LOG_STATS": lambda: _get_bool_from_env("MIS_DISABLE_LOG_STATS", False),
    "MIS_API_KEY": lambda: _get_str_from_env("MIS_API_KEY", None),
    "MIS_DISABLE_FASTAPI_DOCS": lambda: _get_bool_from_env("MIS_DISABLE_FASTAPI_DOCS", False),

    "MIS_ALLOWED_LOCAL_MEDIA_PATH": lambda: _get_str_from_env("MIS_ALLOWED_LOCAL_MEDIA_PATH", "/opt"),
    "MIS_LIMIT_IMAGE_PER_PROMPT": lambda: _get_int_from_env("MIS_LIMIT_IMAGE_PER_PROMPT", 1, 0, 10),
    "MIS_LIMIT_VIDEO_PER_PROMPT": lambda: _get_int_from_env("MIS_LIMIT_VIDEO_PER_PROMPT", 1, 0, 10),
    "MIS_LIMIT_AUDIO_PER_PROMPT": lambda: _get_int_from_env("MIS_LIMIT_AUDIO_PER_PROMPT", 0, 0, 10),

    "UVICORN_LOG_LEVEL": lambda: _get_str_from_env("UVICORN_LOG_LEVEL", "info", constants.UVICORN_LOG_LEVELS),
}


def _get_bool_from_env(name: str, default: Optional[bool]) -> Optional[bool]:
    if name not in os.environ:
        return default
    return os.environ[name].lower() in ["true", "1"]


def _get_int_from_env(name: str, default: Optional[int],
                      min_value: int = None, max_value: int = None, valid_values: list[int] = None) -> Optional[int]:
    if name not in os.environ:
        return default
    try:
        value = int(os.environ[name])
    except ValueError as e:
        raise ValueError(f"ENV {name} is not a valid int value") from e
    EnvChecker.check_int(name, value, min_value, max_value, valid_values)
    return value


def _get_str_from_env(name: str, default: Optional[str], valid_values: list[str] = None) -> Optional[str]:
    if name not in os.environ:
        return default
    value = os.environ[name]
    EnvChecker.check_str_in(name, value, valid_values)
    return value


def _get_cache_path_from_env(name: str, default: str) -> str:
    cache_path = _get_str_from_env(name, default)
    EnvChecker.check_cache_path(name, cache_path)
    return cache_path


def _get_file_from_env(name: str, default: Optional[str] = None) -> Optional[str]:
    file = _get_str_from_env(name, default)
    if file is not None:
        EnvChecker.check_file(name, file)
    return file


def _get_ip_address_from_env(name: str, default: Optional[str] = None) -> Optional[str]:
    ip_address = _get_str_from_env(name, default)
    if ip_address is not None:
        EnvChecker.check_ip_address(name, ip_address)
    return ip_address


def _get_optimization_config():
    return _get_str_from_env("MIS_CONFIG", "atlas800ia2-1x32gb-bf16-vllm-default", valid_values=None)


def _get_ssl_cert_reqs():
    return _get_int_from_env("MIS_SSL_CERT_REQS", int(ssl.CERT_NONE), valid_values=constants.SSL_CERT_REQS_TYPES)


def __getattr__(name):
    if name in environment_variables:
        return environment_variables[name]()
    raise AttributeError(f"module {__name__!r} has no attributes {name!r}")


def __dir__():
    return list(environment_variables.keys())
