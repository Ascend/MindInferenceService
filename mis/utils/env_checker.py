import ipaddress
import re
from pathlib import Path

from mis.logger import init_logger

logger = init_logger(__name__)

class EnvChecker:
    @staticmethod
    def check_float(name: str, num: float,
                    min_value: float = None, max_value: float = None, valid_values: list[float] = None):
        if min_value is not None and num < min_value:
            raise ValueError(f"{name} must be greater than or equal to {min_value}")
        if max_value is not None and num > max_value:
            raise ValueError(f"{name} must be less than or equal to {max_value}")
        if valid_values is not None and num not in valid_values:
            raise ValueError(f"{name}must be one of {valid_values}")
        
    @staticmethod
    def check_string_input(input_string: str, input_string_name: str):
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