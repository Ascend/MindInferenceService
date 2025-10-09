# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import ipaddress
import os
from pathlib import Path
from typing import Tuple

MAX_PATH_LEN = 128


class EnvChecker:

    @staticmethod
    def check_cache_path(name: str, cache_path: str) -> None:
        """Check the validity of the cache path.
        Args:
            name (str): The name of the environment variable.
            cache_path (str): The path to the cache directory.
        Raises:
            ValueError: If the cache path is not an absolute path.
            ValueError: If the length of the cache path exceeds the maximum allowed length.
            ValueError: If the cache path is a symlink.
            ValueError: If the cache path exists but is a file.
        """
        path = Path(cache_path)
        if not path.is_absolute():
            raise ValueError(f"ENV {name} is not an absolute path")
        if len(cache_path) > MAX_PATH_LEN:
            raise ValueError(f"ENV {name} length exceed limit {MAX_PATH_LEN}")
        if path.is_symlink():
            raise ValueError(f"ENV {name} is a symlink")
        if path.exists() and path.is_file():
            raise ValueError(f"ENV {name} exists but is a file")

    @staticmethod
    def check_file(name: str, file: str) -> None:
        """Check the validity of a file path.
        Args:
            name (str): The name of the environment variable.
            file (str): The path to the file.
        Raises:
            ValueError: If the absolute file path length exceeds the maximum limit.
            ValueError: If the file path is a symlink.
            FileNotFoundError: If the file does not exist.
            ValueError: If the file path is not a file.
            PermissionError: If the owner of the file path is not the current user.
            OSError: If an error occurs when checking file path ownership.
        """
        path = Path(file)
        abs_path = path.absolute()
        if len(str(abs_path)) > MAX_PATH_LEN:
            raise ValueError(f"ENV {name} absolute path length exceed limit {MAX_PATH_LEN}")
        if path.is_symlink():
            raise ValueError(f"ENV {name} is a symlink")
        if not path.exists():
            raise FileNotFoundError(f"ENV {name} is not found")
        if not path.is_file():
            raise ValueError(f"ENV {name} is not a file")
        try:
            current_user_id = os.getuid()
            path_stat = os.stat(path)
            path_owner_id = path_stat.st_uid
            if current_user_id != path_owner_id:
                raise PermissionError("File path is not owned by the current user.")
        except OSError as e:
            raise OSError("Error checking ownership of file path.") from e

    @staticmethod
    def check_int(name: str, num: int,
                  min_value: int = None, max_value: int = None, valid_values: Tuple[int] = None) -> None:
        """Check the validity of an integer value.
        Args:
            name (str): The name of the environment variable.
            num (int): The integer value to check.
            min_value (int, optional): The minimum allowed value. Defaults to None.
            max_value (int, optional): The maximum allowed value. Defaults to None.
            valid_values (Tuple[int], optional): A tuple of valid values. Defaults to None.
        Raises:
            ValueError: If the value is less than the minimum allowed value.
            ValueError: If the value is greater than the maximum allowed value.
            ValueError: If the value is not in the list of valid values.
        """
        if min_value is not None and min_value > num:
            raise ValueError(f"ENV {name} less than {min_value}")
        if max_value is not None and max_value < num:
            raise ValueError(f"ENV {name} greater than {max_value}")
        if valid_values is not None and all([num != valid_value for valid_value in valid_values]):
            raise ValueError(f"ENV {name} not in {valid_values}")

    @staticmethod
    def check_str_in(name: str, value: str, valid_values: Tuple[str] = None) -> None:
        """Check the validity of a string value.
        Args:
            name (str): The name of the environment variable.
            value (str): The string value to check.
            valid_values (Tuple[str], optional): A tuple of valid values. Defaults to None.
        Raises:
            ValueError: If the value is not in the list of valid values.
        """
        if valid_values is not None and value not in valid_values:
            raise ValueError(f"ENV {name} not in {valid_values}")

    @staticmethod
    def check_ip_address(name: str, address: str) -> None:
        """Check the validity of an IP address.
        Args:
            name (str): The name of the environment variable.
            address (str): The IP address to check.
        Raises:
            ValueError: If the IP address is not valid.
        """
        try:
            ipaddress.ip_address(address)
        except ValueError as e:
            raise ValueError(f"ENV {name} is not a valid ip address") from e
