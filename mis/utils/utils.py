#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import math
import ipaddress
import os
import re
from pathlib import Path
from typing import Union, Tuple

from fastapi import Request

import mis.envs as envs
from mis.constants import HW_910B
from mis.logger import init_logger, LogType

logger = init_logger(__name__, log_type=LogType.SERVICE)


class ConfigChecker:
    @staticmethod
    def is_value_in_range(name: str, value: Union[int, float],
                          min_value: Union[int, float], max_value: Union[int, float]) -> bool:
        """
        Check if the value is in the range.
        :param name: The name of the value.
        :param value: The value to check.
        :param min_value: The minimum value allowed.
        :param max_value: The maximum value allowed.
        :return: True if the value is in the range, False otherwise.
        """
        if not isinstance(value, (int, float)) or (min_value > max_value):
            logger.warning(f"{name} verification failed!")
            return False

        if isinstance(value, float) and math.isnan(value):
            logger.warning(f"Invalid {name} cannot be NaN")
            return False
        if value < min_value:
            logger.warning(f"{name} must be greater than or equal to {min_value}")
        elif value > max_value:
            logger.warning(f"{name} must be less than or equal to {max_value}")
        else:
            return True
        return False

    @staticmethod
    def is_value_in_enum(name: str, value: Union[int, str, bool], valid_values: Tuple[Union[int, str, bool]]) -> bool:
        """
        Check if the value is in the valid values
        :param name: name of the value
        :param value: value to check
        :param valid_values: tuple of valid values
        :return: True if the value is in the valid values, False otherwise
        """
        if value not in valid_values:
            logger.warning(f"{name} must be one of {valid_values}")
            return False
        return True

    @staticmethod
    def check_string_input(name: str, string: str) -> None:
        """
        Check if the input string is a string and not empty.
        If it is not a string or contains newline characters or space, raise an error.
        :param name: The name of the input string.
        :param string: The input string to check.
        """
        # Verify that the input string is a string
        if not isinstance(string, str):
            logger.error(f"Invalid {name} type: {type(string)}, only str is supported.")
            raise ValueError(f"Invalid {name} type: {type(string)}, only str is supported.")

        # Verify that the input string is not empty
        if not string.strip():
            logger.error(f"Invalid {name} cannot be empty")
            raise ValueError(f"Invalid {name} cannot be empty")

        # Verify that the input string does not contain any special characters
        pattern_risk = '[^\w\-\/]'  # Only letters, numbers, '_', '-', and '/' are allowed
        compile_pattern = re.compile(pattern_risk)
        if compile_pattern.search(string):
            logger.error(f"The parameter args.{name} cannot contain special characters "
                         "other than '-', '/'")
            raise ValueError(f"The parameter args.{name} cannot contain special characters "
                             "other than '-', '/'")


def get_soc_name() -> Union[str, None]:
    try:
        import acl
        soc_info = acl.get_soc_name()
    except ImportError as e:
        logger.error(f"Unable to import ACL: {e}, please check if ACL is imported correctly.")
        raise ImportError("Unable to import ACL, please check if ACL is imported correctly.") from e
    except Exception as e:
        logger.error(f"get soc info failed: {e}, please check if CANN is installed correctly.")
        raise Exception("get soc info failed, please check if CANN is installed correctly.") from e
    if soc_info is None:
        logger.error("get soc info failed, please check the device mounting status.")
        raise RuntimeError("get soc info failed, please check the device mounting status.")
    elif HW_910B in soc_info:
        logger.info(f"Detected SOC: {HW_910B}")
        return HW_910B
    else:
        logger.info("No matching SOC found")
        return None


def get_model_path(raw_model: str) -> str:
    """Get model path from raw_model.
    given raw_model a `Qwen3-8B` style str, this function will find
        absolute path of exist model to that path.
    return this absolute path.
    """
    abs_model_path = Path(envs.MIS_CACHE_PATH).joinpath(raw_model)

    if not abs_model_path.exists():
        logger.error("Local model path does not exist.")
        raise FileNotFoundError("Local model path does not exist.")

    if not abs_model_path.is_dir():
        logger.error("Local model path is not a directory.")
        raise NotADirectoryError("Local model path is not a directory.")

    if abs_model_path.is_symlink():
        logger.error("Local model path is a symlink.")
        raise FileNotFoundError("Local model path is a symlink.")

    if not os.access(abs_model_path, os.R_OK):
        logger.error("Local model path is not readable.")
        raise PermissionError("Local model path is not readable.")

    try:
        current_user_id = os.getuid()
        path_stat = os.stat(abs_model_path)
        path_owner_id = path_stat.st_uid
        if current_user_id != path_owner_id:
            raise PermissionError("File path is not owned by the current user.")
    except OSError as e:
        raise OSError("Error checking ownership of file path.") from e

    logger.info("Model path is valid and readable.")
    return str(abs_model_path)


def get_client_ip(request: Request) -> str:
    """Get client IP address
    Args:
        request: The request object from which to extract the client IP address.
    """
    if not isinstance(request, Request):
        logger.error("Invalid request type")
        raise TypeError("Invalid request type")
    # Check X-Forwarded-For header
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
    else:
        # Check X-Real-IP header
        client_ip = request.headers.get("X-Real-IP", request.client.host if request.client else "unknown")

    if client_ip == "unknown":
        logger.warning(f"Could not determine valid client IP from any source, return unknown.")
    else:
        try:
            ipaddress.ip_address(client_ip)
        except ValueError:
            logger.warning(f"Get invalid IP address, return unknown.")
            client_ip = "unknown"

    return client_ip
