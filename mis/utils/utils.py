# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import re
from typing import List, Union

from mis.logger import init_logger

logger = init_logger(__name__)


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
        if not (type(value) == type(min_value) == type(max_value)) or (min_value > max_value):
            logger.warning(f"{name} verification failed!")
        
        if value < min_value:
            logger.warning(f"{name} must be greater than or equal to {min_value}")
        elif value > max_value:
            logger.warning(f"{name} must be less than or equal to {max_value}")
        else:
            return True
        return False
    @staticmethod
    def is_value_in_enum(name: str, value: Union[int, str, bool], valid_values: List[Union[int, str, bool]]):
        """
        Check if the value is in the valid values
        :param name: name of the value
        :param value: value to check
        :param valid_values: list of valid values
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
