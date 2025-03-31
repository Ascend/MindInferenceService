# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import logging
from logging import Logger
from logging.config import dictConfig

import mis.envs as envs

MIS_LOG_LEVEL = envs.MIS_LOG_LEVEL

_FORMAT = "%(levelname)s %(asctime)s %(filename)s:%(lineno)d] %(message)s"
_DATE_FORMAT = "%m-%d %H:%M:%S"

DEFAULT_LOGGING_CONFIG = {
    "formatters": {
        "mis": {
            "class": "mis.utils.logger_utils.NewLineFormatter",
            "datefmt": _DATE_FORMAT,
            "format": _FORMAT,
        },
    },
    "handlers": {
        "mis": {
            "class": "logging.StreamHandler",
            "formatter": "mis",
            "level": MIS_LOG_LEVEL,
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "mis": {
            "handlers": ["mis"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
    "version": 1,
    "disable_existing_loggers": False
}


def _configure_mis_root_logger() -> None:
    dictConfig(DEFAULT_LOGGING_CONFIG)


_configure_mis_root_logger()


def init_logger(name: str) -> Logger:
    return logging.getLogger(name)
