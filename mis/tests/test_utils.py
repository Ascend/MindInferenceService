#!/usr/bin/env python
# coding=utf-8
"""
-------------------------------------------------------------------------
This file is part of the Mind Inference Service project.
Copyright (c) 2025 Huawei Technologies Co.,Ltd.

Mind Inference Service is licensed under Mulan PSL v2.
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
import unittest
from unittest.mock import MagicMock

from fastapi import Request
from mis.utils.utils import get_client_ip, ConfigChecker


class TestConfigChecker(unittest.TestCase):

    def test_is_value_in_range(self):
        # Test if value is within the valid range
        self.assertTrue(ConfigChecker.is_value_in_range("test", 5, 1, 10))
        # Test boundary condition: minimum value
        self.assertTrue(ConfigChecker.is_value_in_range("test", 1, 1, 10))
        # Test boundary condition: maximum value
        self.assertTrue(ConfigChecker.is_value_in_range("test", 10, 1, 10))
        # Test value below the minimum
        self.assertFalse(ConfigChecker.is_value_in_range("test", 0, 1, 10))
        # Test value above the maximum
        self.assertFalse(ConfigChecker.is_value_in_range("test", 11, 1, 10))
        # Test min_value is greater than max_value and value is within the valid range
        self.assertFalse(ConfigChecker.is_value_in_range("test", 5, 10, 1))
        # Test min_value is greater than max_value and value above the minimum
        self.assertFalse(ConfigChecker.is_value_in_range("test", 11, 10, 1))
        # Test min_value is greater than max_value and value below the maximum
        self.assertFalse(ConfigChecker.is_value_in_range("test", 0, 10, 1))
        # Test value is NaN
        self.assertFalse(ConfigChecker.is_value_in_range("test", float('nan'), 1, 10))

    def test_is_value_in_enum(self):
        valid_values = [1, 2, 3]
        # Test valid value
        self.assertTrue(ConfigChecker.is_value_in_enum("test", 2, valid_values))
        # Test invalid value
        self.assertFalse(ConfigChecker.is_value_in_enum("test", 4, valid_values))

    def test_check_string_input(self):
        # Test valid string
        ConfigChecker.check_string_input("test", "valid_string")
        # Test empty string
        with self.assertRaises(ValueError):
            ConfigChecker.check_string_input("test", "")
        # Test string with special characters
        with self.assertRaises(ValueError):
            ConfigChecker.check_string_input("test", "invalid!string")


class TestFileOperations(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_json_path = "test.json"
        self.test_data = {"key": "value"}

    def tearDown(self):
        if os.path.exists(self.test_json_path):
            os.remove(self.test_json_path)


class TestGetClientIP(unittest.TestCase):

    def test_get_client_ip_with_client_host(self):
        """Test getting client IP from request.client.host"""
        # Create mock request
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        ip = get_client_ip(request)
        self.assertEqual(ip, "127.0.0.1")

    def test_get_client_ip_with_invalid_ip(self):
        """Test getting invalid client IP from request.client.host"""
        # Create mock request
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "300.0.0.1"

        ip = get_client_ip(request)
        self.assertEqual(ip, "unknown")


if __name__ == "__main__":
    unittest.main()
