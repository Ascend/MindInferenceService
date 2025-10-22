# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import unittest
from unittest.mock import MagicMock

from fastapi import Request

from mis.utils.utils import (
    ConfigChecker,
    ContainerIPDetector,
    get_client_ip
)


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


class TestContainerIP(unittest.TestCase):
    def test_get_container_ip_from_env_success(self):
        os.environ['CONTAINER_IP'] = '192.168.1.1'
        os.environ['POD_IP'] = '192.168.1.2'
        os.environ['HOST_IP'] = '192.168.1.3'

        with self.assertLogs('mis.utils.utils', level='INFO') as cm:
            ip = ContainerIPDetector._get_container_ip_from_env()
            self.assertEqual(ip, '192.168.1.1')
            expected_message = "IP obtained from environment variable"
            self.assertTrue(any(expected_message in log_output for log_output in cm.output),
                            f"Expected message '{expected_message}' not found in log output.")

    def test_get_container_ip_from_env_failure(self):
        if 'CONTAINER_IP' in os.environ:
            del os.environ['CONTAINER_IP']
        if 'POD_IP' in os.environ:
            del os.environ['POD_IP']
        if 'HOST_IP' in os.environ:
            del os.environ['HOST_IP']

        with self.assertLogs('mis.utils.utils', level='INFO') as cm:
            ip = ContainerIPDetector._get_container_ip_from_env()
            self.assertIsNone(ip)
            expected_message = "Failed to obtain IP from environment variables"
            self.assertTrue(any(expected_message in log_output for log_output in cm.output),
                            f"Expected message '{expected_message}' not found in log output.")


class TestFileOperations(unittest.TestCase):
    def setUp(self):
        self.test_json_path = "test.json"
        self.test_data = {"key": "value"}

    def tearDown(self):
        if os.path.exists(self.test_json_path):
            os.remove(self.test_json_path)


class TestGetClientIP(unittest.TestCase):
    def test_get_client_ip_with_x_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For header"""

        # Create mock request
        request = MagicMock(spec=Request)
        request.headers = {"X-Forwarded-For": "192.168.1.100, 10.0.0.1"}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        ip = get_client_ip(request)
        self.assertEqual(ip, "192.168.1.100")

    def test_get_client_ip_with_x_real_ip(self):
        """Test getting client IP from X-Real-IP header"""
        # Create mock request
        request = MagicMock(spec=Request)
        request.headers = {"X-Real-IP": "192.168.1.100"}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        ip = get_client_ip(request)
        self.assertEqual(ip, "192.168.1.100")

    def test_get_client_ip_with_client_host(self):
        """Test getting client IP from request.client.host"""
        # Create mock request
        request = MagicMock(spec=Request)
        request.headers = {}
        request.client = MagicMock()
        request.client.host = "127.0.0.1"

        ip = get_client_ip(request)
        self.assertEqual(ip, "127.0.0.1")

if __name__ == "__main__":
    unittest.main()
