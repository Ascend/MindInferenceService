#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import importlib.metadata
import ipaddress
import math
import os
import re
from pathlib import Path
from typing import Any, Tuple, Union

import json

import mis.envs as envs
from mis.constants import HW_910B, DIRECTORY_PERMISSIONS
from mis.logger import init_logger, LogType
from mis.utils.general_checker import GeneralChecker

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
        if not isinstance(value, (int, str, bool)):
            logger.warning(f"{name} verification failed!")
            return False
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
        logger.error("Unable to import ACL, please check if ACL is imported correctly.")
        raise ImportError("Unable to import ACL, please check if ACL is imported correctly.") from e
    except Exception as e:
        logger.error("get soc info failed, please check if CANN is installed correctly.")
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
    try:
        expected_mode = DIRECTORY_PERMISSIONS  # 750
        GeneralChecker.check_path_or_file(
            path_label="Local model path",
            path=str(abs_model_path),
            is_dir=True,
            expected_mode=expected_mode
        )
        if not os.access(abs_model_path, os.R_OK):
            logger.error("Local model path is not readable by current process.")
            raise OSError("Local model path is not readable by current process.")
    except OSError as e:
        logger.error("Error checking ownership of file path.")
        raise OSError("Error checking ownership of file path.") from e
    except Exception as e:
        logger.error("Unexpected error while get model path.")
        raise Exception("Unexpected error while get model path.") from e
    logger.info("Model path is valid and readable.")
    return str(abs_model_path)


def get_client_ip(request) -> str:
    """Get client IP address
    Args:
        request: The request object from which to extract the client IP address.
    """
    try:
        from fastapi import Request
    except ImportError as e:
        logger.warning(f"Failed to import fastapi.Request: {e}")
        raise ImportError("Failed to import fastapi.Request. Please ensure fastapi is installed.") from e

    if not isinstance(request, Request):
        logger.error("Invalid request type")
        raise TypeError("Invalid request type")

    try:
        client_ip = request.client.host
        try:
            ipaddress.ip_address(client_ip)
        except ValueError:
            logger.warning("Get invalid IP address, return unknown.")
            client_ip = "unknown"
    except AttributeError as e:
        logger.error("Error getting client IP address.")
        raise AttributeError("Error getting client IP address.") from e
    except Exception as e:
        logger.error("Unexpected error while getting client IP address.")
        raise Exception("Unexpected error while getting client IP address.") from e

    return client_ip


def get_vllm_version():
    try:
        return importlib.metadata.version("vllm")
    except importlib.metadata.PackageNotFoundError:
        return None


def convert_string_to_dict(obj: Any, depth: int = 0, max_depth: int = 10):
    """
    Convert a string to a dictionary.
    Args: obj (str): The string to convert.
          depth (int): The current depth of recursion.
          max_depth (int): The maximum depth of recursion.
    Returns: Dict[str, Any]: The converted dictionary.
    """
    if isinstance(obj, dict):
        return {k: convert_string_to_dict(v, depth+1, max_depth) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_string_to_dict(item, depth+1, max_depth) for item in obj]
    elif isinstance(obj, str):
        try:
            parsed = json.loads(obj)
            if isinstance(parsed, (dict, list)):
                return convert_string_to_dict(parsed, depth+1, max_depth)
            else:
                return parsed
        except json.JSONDecodeError:
            return obj
        except ValueError:
            return obj
    else:
        return obj
