# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

import mis.constants as constants
from mis.utils.env_checker import EnvChecker

DEFAULT_MIS_MODEL = "Qwen3-8B"
DEFAULT_MIS_CONFIG = "atlas800ia2-1x32gb-bf16-vllm-default"

if TYPE_CHECKING:
    MIS_CACHE_PATH: str = "/opt/mis/.cache"
    MIS_MODEL: str = DEFAULT_MIS_MODEL
    MIS_ENGINE_TYPE: str = "vllm"
    MIS_CONFIG: str = DEFAULT_MIS_CONFIG

    MIS_PORT: int = 8000
    MIS_ENABLE_DOS_PROTECTION: bool = True
    MIS_LOG_LEVEL: str = "INFO"
    MIS_MAX_LOG_LEN: Optional[int] = 2048

    UVICORN_LOG_LEVEL: str = "info"

environment_variables: Dict[str, Callable[[], Any]] = {
    "MIS_CACHE_PATH": lambda: _get_cache_path_from_env("MIS_CACHE_PATH", "/opt/mis/.cache"),
    "MIS_MODEL": lambda: _get_str_from_env("MIS_MODEL", DEFAULT_MIS_MODEL, constants.MIS_MODEL_LIST),
    "MIS_ENGINE_TYPE": lambda: _get_str_from_env("MIS_ENGINE_TYPE", "vllm", constants.MIS_ENGINE_TYPES),
    "MIS_CONFIG": lambda: _get_str_from_env("MIS_CONFIG", DEFAULT_MIS_CONFIG, constants.MIS_CONFIGS_LIST),

    "MIS_PORT": lambda: _get_int_from_env("MIS_PORT", 8000, 1024, 65535),
    "MIS_ENABLE_DOS_PROTECTION": lambda: _get_bool_from_env("MIS_ENABLE_DOS_PROTECTION", True),
    "MIS_LOG_LEVEL": lambda: _get_str_from_env("MIS_LOG_LEVEL", "INFO", constants.MIS_LOG_LEVELS),
    "MIS_MAX_LOG_LEN": lambda: _get_int_from_env("MIS_MAX_LOG_LEN", 2048, min_value=0, max_value=8192),

    "UVICORN_LOG_LEVEL": lambda: _get_str_from_env("UVICORN_LOG_LEVEL", "info", constants.UVICORN_LOG_LEVELS),

}


def _get_bool_from_env(name: str, default: Optional[bool]) -> Optional[bool]:
    if name not in os.environ:
        return default
    return os.environ[name].lower() in ["true", "1"]


def _get_int_from_env(name: str, default: Optional[int],
                      min_value: int = None, max_value: int = None, valid_values: tuple[int] = None) -> Optional[int]:
    if name not in os.environ:
        return default
    try:
        value = int(os.environ[name])
    except ValueError as e:
        raise ValueError(f"ENV {name} is not a valid int value") from e
    EnvChecker.check_int(name, value, min_value, max_value, valid_values)
    return value


def _get_str_from_env(name: str, default: Optional[str], valid_values: tuple[str] = None) -> Optional[str]:
    if name not in os.environ:
        return default
    value = os.environ[name]
    EnvChecker.check_str_in(name, value, valid_values)
    return value


def _get_cache_path_from_env(name: str, default: str) -> str:
    cache_path = _get_str_from_env(name, default)
    EnvChecker.check_cache_path(name, cache_path)
    return cache_path


def __getattr__(name: str) -> Any:
    if name in environment_variables:
        return environment_variables[name]()
    raise AttributeError(f"module {__name__!r} has no attributes {name!r}")


def __dir__() -> list[str]:
    return list(environment_variables.keys())
