# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import re

from mis.logger import init_logger

logger = init_logger(__name__)


class ConfigChecker:

    @staticmethod
    def validate_value(name: str, value, value_type, min_value=None, max_value=None, valid_values=None):
        if not isinstance(value, value_type):
            logger.warning(f"{name} must be a {value_type.__name__}, but got {type(value).__name__}")
            return False
        
        if min_value is not None and not isinstance(min_value, (int, float)):
            logger.warning(f"min_value for {name} must be a number, but got {type(min_value).__name__}")
            return False
        
        if max_value is not None and not isinstance(max_value, (int, float)):
            logger.warning(f"max_value for {name} must be a number, but got {type(max_value).__name__}")
            return False
        
        if min_value is not None and max_value is not None and min_value > max_value:
            logger.warning(f"Invalid range for {name}: min_value ({min_value}) should be " 
                           f"less than or equal to max_value ({max_value})")
            return False
        
        is_valid = True
        if min_value is not None and value < min_value:
            logger.warning(f"{name} must be greater than or equal to {min_value}")
            is_valid = False
        if max_value is not None and value > max_value:
            logger.warning(f"{name} must be less than or equal to {max_value}")
            is_valid = False
        if valid_values is not None:
            if not isinstance(valid_values, list) or not all(isinstance(v, value_type) for v in valid_values):
                logger.warning(f"valid_values for {name} must be a list of {value_type.__name__}, " 
                               f"but got {type(valid_values).__name__}")
                return False
            if value not in valid_values:
                logger.warning(f"{name} must be one of {valid_values}")
                is_valid = False
        
        return is_valid

    @staticmethod
    def is_int_value_in_range(name: str, value: int, min_value: int = None, max_value: int = None, 
                              valid_values: list[int] = None):
        return ConfigChecker.validate_value(name, value, int, min_value, max_value, valid_values)

    @staticmethod
    def is_float_value_in_range(name: str, value: float, min_value: float = None, max_value: float = None, 
                                valid_values: list[float] = None):
        return ConfigChecker.validate_value(name, value, (int, float), min_value, max_value, valid_values)

    @staticmethod
    def is_bool_value_in_range(name: str, value: bool, valid_values: list[bool]):
        if not isinstance(name, str) or not isinstance(value, bool) or not all(
            isinstance(v, bool) for v in valid_values):
            logger.warning("Invalid parameter types")
            return False

        if value not in valid_values:
            logger.warning(f"{name} must be one of {valid_values}")
            return False
        return True

    @staticmethod
    def is_str_value_in_range(name: str, value: str, valid_values: list[str]):
        if not isinstance(name, str) or not isinstance(valid_values, list) or not all(
            isinstance(v, str) for v in valid_values):
            logger.warning("Invalid parameter types")
            return False
        
        if value is not None and value not in valid_values:
            logger.warning(f"{name}={value} not in {valid_values}")
            return False
        return True

    @staticmethod
    def check_string_input(input_string_name: str, input_string: str):
        """
        Check if the input string is a string and not empty.
        If it is not a string or contains newline characters or space, raise an error.
        :param input_string: The input string to check.
        :param input_string_name: The name of the input string.
        """
        # Verify that the input string is a string
        if not isinstance(input_string, str):
            logger.error(f"Invalid {input_string_name} type: {type(input_string)}, only str is supported.")
            raise ValueError(f"Invalid {input_string_name} type: {type(input_string)}, only str is supported.")
        
        # Verify that the input string is not empty
        if not input_string.strip():
            logger.error(f"Invalid {input_string_name} cannot be empty")
            raise ValueError(f"Invalid {input_string_name} cannot be empty")
        
        # Verify that the input string does not contain any special characters
        pattern_risk = '[\n\s]'
        compile_pattern = re.compile(pattern_risk)
        if compile_pattern.search(input_string):
            logger.error(f"The parameter args.{input_string_name} cannot contain newlines or spaces")
            raise ValueError(f"The parameter args.{input_string_name} cannot contain newlines or spaces")
