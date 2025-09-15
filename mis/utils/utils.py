# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import importlib
import os
import re
from typing import List, Union, Optional, Tuple

import json
import socket
from vllm.config import VllmConfig

from mis.constants import HW_310P, HW_910B
from mis.logger import init_logger


logger = init_logger(__name__)


ENV_CONTAINER_VARS = ('CONTAINER_IP', 'POD_IP', 'HOST_IP')


class ConfigChecker:
    @staticmethod
    def is_value_in_range(name: str, value: Union[int, float],
                          min_value: Union[int, float], max_value: Union[int, float]):
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
        
        if value < min_value:
            logger.warning(f"{name} must be greater than or equal to {min_value}")
        elif value > max_value:
            logger.warning(f"{name} must be less than or equal to {max_value}")
        else:
            return True
        return False

    @staticmethod
    def is_value_in_enum(name: str, value: Union[int, str, bool], valid_values: Tuple[Union[int, str, bool]]):
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
    def check_string_input(name: str, string: str):
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
        pattern_risk = '[^\w\-\/]' # Only letters, numbers, '_', '-', and '/' are allowed
        compile_pattern = re.compile(pattern_risk)
        if compile_pattern.search(string):
            logger.error(f"The parameter args.{name} cannot contain special characters "
                          "other than '-', '/'")
            raise ValueError(f"The parameter args.{name} cannot contain special characters "
                              "other than '-', '/'")


def _log_and_raise(logger_: logger, error_message: str, exception_class) -> None:
    logger_.error(error_message)
    raise exception_class(error_message)


def set_config_perm(model_path: str, mode: int = 0o750) -> None:
    """Model config permission setting for MindIE-Service Backend
    :param: model_path: model path
    """
    if not isinstance(model_path, str):
        _log_and_raise(logger,
                       f"Invalid model_path type: {type(model_path)}, only str is supported.",
                       ValueError)

    config_path = os.path.join(model_path, "config.json")
    try:
        if not os.path.exists(config_path):
            _log_and_raise(logger,
                           f"Model config file does not exist, "
                           f"please check the integrity of the model repository",
                           FileNotFoundError)

        os.chmod(config_path, mode)
    except PermissionError as e:
        _log_and_raise(logger, f"Failed to set the permission of the model config file: {e}",
                       PermissionError)
    except Exception as e:
        _log_and_raise(logger,
                       f"An error occurred while setting the permission of the model config file: {e}",
                      Exception)


def read_json(json_path: str) -> Union[str, dict, list]:
    """
    Read config file content
    :param json_path: Path to JSON file
    :return: Content of the JSON file as a str, dictionary or list
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        logger.error(f"Failed to read JSON file: {str(e)}")
        raise RuntimeError("Failed to read JSON file") from e
    return json_data


def write_json(json_path: str, json_data: Union[str, dict, list]) -> None:
    """
    Write modified config back to file
    :param json_path: Path to JSON file
    :param json_data: Data to write to the JSON file
    """
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
            f.write('\n')
        logger.info(f"JSON file written to: {json_path}")
    except Exception as e:
        logger.error(f"Save failed: {str(e)}")
        raise RuntimeError("JSON file write operation failed") from e


def get_soc_name() -> Union[str, None]:
    try:
        import acl
        soc_info = acl.get_soc_name()
    except Exception as e:
        logger.error(f"get soc info failed: {e}, please check if CANN is installed correctly.")
        raise Exception("get soc info failed, please check if CANN is installed correctly.") from e
    if soc_info is None:
        logger.error("get soc info failed, please check the device mounting status.")
        raise RuntimeError("get soc info failed, please check the device mounting status.")
    if HW_310P in soc_info:
        return HW_310P
    elif HW_910B in soc_info:
        return HW_910B
    else:
        return None


def check_dependencies(required_packages: list) -> None:
    missing_packages = []

    for package in required_packages:
        if importlib.util.find_spec(package) is None:
            missing_packages.append(package)

    if missing_packages:
        logger.warning(f"The following required packages are missing: {', '.join(missing_packages)}")


def vllm_v1_supported(engine_config: VllmConfig) -> Optional[bool]:
    v1_params = ['model_config', 'cache_config', 'parallel_config']
    engine_config_dict = vars(engine_config)
    v1_supported = any(param in engine_config_dict for param in v1_params)
    try:
        v1_supported = v1_supported and "v1" in engine_config.parallel_config.worker_cls
    except AttributeError:
        logger.warning("Unable to detect vLLM engine version (V0 / V1). "
                       "Please check the engine environment variables corresponding to the vllm version and "
                       "the model support provided by the vLLM engine.")
        return None
    return v1_supported


class ContainerIPDetector:
    """Detects the container's IP address at environment preparation."""
    @staticmethod
    def _get_hostname_ip() -> Optional[str]:
        """Get IP address using the hostname method."""
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            logger.info(f"IP obtained through hostname")
            return ip
        except Exception as e:
            logger.warning(f"Failed to obtain IP through hostname")
            return None

    @staticmethod
    def _get_container_ip_from_env() -> Optional[str]:
        """Get container IP from environment variables."""
        # Some container orchestration systems set these environment variables
        env_vars = ENV_CONTAINER_VARS
        for var in env_vars:
            ip = os.environ.get(var)
            if ip:
                logger.info(f"IP obtained from environment variable")
                return ip
        logger.info("Failed to obtain IP from environment variables")
        return None

    @classmethod
    def get_ip(cls, ip_current) -> Optional[str]:
        """Run IP detection and return the primary IP."""
        if ip_current is not None and ip_current != "0.0.0.0":
            return ip_current

        # Fallback to hostname IP
        primary_ip = cls._get_hostname_ip()
        if primary_ip:
            return primary_ip

        # Fallback to environment variable IP
        primary_ip = cls._get_container_ip_from_env()
        if primary_ip:
            return primary_ip

        logger.warning("Failed to detect primary IP address")
        return None


def check_files_number(files_list: List[str], expected_number: int) -> None:
    if len(files_list) > expected_number:
        logger.error(f"Number of files exceeds the maximum allowed count of {expected_number}")
        raise ValueError(f"Number of files exceeds the maximum allowed count of {expected_number}")


def check_file_size(file_path: str, max_file_size: int) -> None:
    try:
        file_size = os.path.getsize(file_path)
    except OSError as e:
        file_size = 0
        logger.error(f"Failed to get the size of file {file_path}")
    if file_size > max_file_size:
        logger.error(f"File {file_path} exceeds the maximum allowed size of {max_file_size} bytes")
        raise ValueError(f"File {file_path} exceeds the maximum allowed size of {max_file_size} bytes")
