#!/usr/bin/env python
# coding=utf-8
"""
-------------------------------------------------------------------------
This file is part of the Mind Inference Service project.
Copyright (c) 2025 Huawei Technologies Co.,Ltd.

MindInferenceService is licensed under Mulan PSL v2.
You can use this software according to the terms and conditions of the Mulan PSL v2.
You may obtain a copy of Mulan PSL v2 at:

         http://license.coscl.org.cn/MulanPSL2

THIS SOFTWARE IS PROVIDED ON AN "AS IS" BASIS, WITHOUT WARRANTIES OF ANY KIND,
EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO NON-INFRINGEMENT,
MERCHANTABILITY OR FIT FOR A PARTICULAR PURPOSE.
See the Mulan PSL v2 for more details.
-------------------------------------------------------------------------
"""
import os
import re
import stat
from typing import Tuple, Optional

MAX_PATH_LEN = 1024


class GeneralChecker:
    @staticmethod
    def check_path_or_file(
        path_label: str,
        path: str,
        is_dir: bool = False,
        expected_mode: int = None,
        max_file_size: Optional[int] = None
    ) -> None:
        """
        Check the validity of a path, including existence, type, permissions, owner, group, etc.
        Args:
            path_label (str): The name of the path (for error messages).
            path (str): The path to check.
            is_dir (bool): Whether the path is expected to be a directory.
            expected_mode (int): Expected file mode (e.g., e.g., stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP for 750).
            max_file_size (Optional[int]): Maximum allowed file size in bytes (default: 1MB).
        """
        GeneralChecker._path_validate_input(path_label, path, is_dir, expected_mode, max_file_size)
        GeneralChecker._check_path_validity(path_label, path)

        if os.path.exists(path):
            if is_dir and not os.path.isdir(path):
                raise OSError(f"{path_label} is not a directory.")
            elif not is_dir and not os.path.isfile(path):
                raise OSError(f"{path_label} is not a file.")

            GeneralChecker._check_path_permissions(path_label, path)

            if expected_mode is not None:
                dir_mode = stat.S_IMODE(os.stat(path).st_mode)
                if dir_mode > expected_mode:
                    raise PermissionError(
                        f"{path_label} has too permissive permissions: {oct(dir_mode)}. "
                        f"Maximum allowed is {oct(expected_mode)}."
                    )
            if max_file_size is not None and os.path.isfile(path):
                file_size = os.path.getsize(path)
                if file_size > max_file_size:
                    raise ValueError(f"{path_label} size exceeds {max_file_size} bytes.")

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
    def _path_validate_input(path_label: str, path: str, is_dir: bool, expected_mode: int, max_file_size: int):
        if not isinstance(path_label, str) or not isinstance(path, str):
            raise TypeError("path_label and path must be a string.")
        if not isinstance(is_dir, bool):
            raise TypeError("is_dir must be a bool.")
        if expected_mode is not None and not isinstance(expected_mode, int):
            raise TypeError("expected_mode must be an int.")
        if max_file_size is not None and not isinstance(max_file_size, int):
            raise TypeError("max_file_size must be an int.")

    @staticmethod
    def _check_path_validity(path_label: str, path: str):
        if len(path) > MAX_PATH_LEN:
            raise ValueError(f"{path_label} is too long, it's length must be less than 1024.")

        pattern_name = re.compile(r"[^0-9a-zA-Z_./-]")
        match_name = pattern_name.findall(path)
        if match_name:
            raise ValueError(f"{path_label} contains illegal characters. Only [a-z A-Z 0-9 _ . / -] are allowed.")

        if ".." in path:
            raise ValueError(f"{path_label} contains '..' characters, which is not allowed.")

        real_path = os.path.realpath(path)
        if real_path != os.path.normpath(path):
            raise OSError(f"{path_label} is link, it's not supported.")

    @staticmethod
    def _check_path_permissions(name: str, path: str):
        """Check if the path is owned by the current user and group.
        Args:
            name (str): The name of the path (for error messages).
            path (str): The path to check.
        """
        try:
            import grp
            import pwd
        except ImportError as e:
            raise ImportError("Failed to import module 'grp' or 'pwd'") from e
        stat_info = os.stat(path)
        current_uid = os.getuid()
        current_user = pwd.getpwuid(current_uid).pw_name
        current_gid = os.getgid()
        current_group = grp.getgrgid(current_gid).gr_name

        file_uid = stat_info.st_uid
        file_user = pwd.getpwuid(file_uid).pw_name
        file_gid = stat_info.st_gid
        file_group = grp.getgrgid(file_gid).gr_name
        if file_uid != current_uid:
            raise PermissionError(f"{name} owner does not match current user ID: {current_uid} != {file_uid}")
        if file_user != current_user:
            raise PermissionError(f"{name} owner does not match current user name: {current_user} != {file_user}")
        if file_gid != current_gid:
            raise PermissionError(f"{name} group does not match current user group ID: {current_gid} != {file_gid}")
        if file_group != current_group:
            raise PermissionError(f"{name} group does not match current user group name: "
                                  f"{current_group} != {file_group}")