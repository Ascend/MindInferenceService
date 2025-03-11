# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import ipaddress
from pathlib import Path

MAX_PATH_LEN = 128


class EnvChecker:

    @staticmethod
    def check_cache_path(name: str, cache_path: str):
        """check cache_path
            1. must be absolute path
            2. length less than MAX_PATH_LEN
            3. can not be symlink
            4. can not be an exist file
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
    def check_file(name: str, file: str):
        """check file
            1. absolute file path length less than MAX_PATH_LEN
            2. can not be symlink
            3. must exist
            4. must be a file
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

    @staticmethod
    def check_int(name: str, num: int,
                  min_value: int = None, max_value: int = None, valid_values: list[int] = None):
        if min_value is not None and min_value > num:
            raise ValueError(f"ENV {name} less than {min_value}")
        if max_value is not None and max_value < num:
            raise ValueError(f"ENV {name} greater than {max_value}")
        if valid_values is not None and all([num != valid_value for valid_value in valid_values]):
            raise ValueError(f"ENV {name} not in {valid_values}")

    @staticmethod
    def check_str_in(name: str, value: str, valid_values: list[str] = None):
        if valid_values is not None and value not in valid_values:
            raise ValueError(f"ENV {name} not in {valid_values}")

    @staticmethod
    def check_ip_address(name: str, address: str):
        try:
            ipaddress.ip_address(address)
        except ValueError as e:
            raise ValueError(f"ENV {name} is not a valid ip address") from e
