# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import tempfile
import unittest

import mis.envs as envs


DEFAULT_IP = "192.168.1.1"


class TestEnvs(unittest.TestCase):

    def setUp(self):
        # Save the original environment variables
        self.original_envs = {key: os.environ.get(key) for key in os.environ}

    def tearDown(self):
        # Restore the original environment variables
        for key, value in self.original_envs.items():
            if value is not None:
                os.environ[key] = value
            else:
                os.environ.pop(key, None)

    def test_get_bool_from_env(self):
        os.environ["TEST_BOOL_TRUE"] = "true"
        os.environ["TEST_BOOL_FALSE"] = "false"
        os.environ["TEST_BOOL_INVALID"] = "invalid"
        self.assertEqual(envs._get_bool_from_env("TEST_BOOL_TRUE", False), True)
        self.assertEqual(envs._get_bool_from_env("TEST_BOOL_FALSE", True), False)
        self.assertEqual(envs._get_bool_from_env("TEST_BOOL_NOT_EXIST", True), True)

    def test_get_int_from_env(self):
        os.environ["TEST_INT_VALID"] = "123"
        os.environ["TEST_INT_INVALID"] = "abc"
        os.environ["TEST_INT_OUT_OF_RANGE"] = "100000"
        self.assertEqual(envs._get_int_from_env("TEST_INT_VALID", 0, 100, 200),
                         123)
        with self.assertRaises(ValueError):
            envs._get_int_from_env("TEST_INT_INVALID", 0)
        with self.assertRaises(ValueError):
            envs._get_int_from_env("TEST_INT_OUT_OF_RANGE", 0, 100, 200)
        self.assertEqual(envs._get_int_from_env("TEST_INT_NOT_EXIST", 456), 456)

    def test_get_str_from_env(self):
        os.environ["TEST_STR_VALID"] = "valid_value"
        os.environ["TEST_STR_INVALID"] = "invalid_value"
        self.assertEqual(envs._get_str_from_env("TEST_STR_VALID", "default"), "valid_value")
        with self.assertRaises(ValueError):
            envs._get_str_from_env("TEST_STR_INVALID", "default", ["valid_value"])
        self.assertEqual(envs._get_str_from_env("TEST_STR_NOT_EXIST", "default"), "default")

    def test_get_cache_path_from_env(self):
        os.environ["TEST_CACHE_PATH_VALID"] = "/valid/path"
        os.environ["TEST_CACHE_PATH_INVALID"] = ("/invalid/invalid/invalid/invalid/invalid/invalid/invalid/invalid/"
                                                 "invalid/invalid/invalid/invalid/invalid/invalid/invalid/invalid/"
                                                 "invalid/invalid/invalid/invalid/invalid/invalid/invalid/invalid/"
                                                 "invalid/invalid/invalid/path")
        self.assertEqual(envs._get_cache_path_from_env("TEST_CACHE_PATH_VALID", "/default/path"),
                         "/valid/path")
        with self.assertRaises(ValueError):
            envs._get_cache_path_from_env("TEST_CACHE_PATH_INVALID", "/default/path")
        self.assertEqual(envs._get_cache_path_from_env("TEST_CACHE_PATH_NOT_EXIST", "/default/path"),
                         "/default/path")

    def test_get_file_from_env(self):
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            os.environ["TEST_FILE_VALID"] = temp_file.name
            os.environ["TEST_FILE_INVALID"] = ("/invalid/invalid/invalid/invalid/invalid/invalid/invalid/invalid/"
                                               "invalid/invalid/invalid/invalid/invalid/invalid/invalid/invalid/"
                                               "invalid/invalid/invalid/invalid/invalid/invalid/invalid/invalid/"
                                               "invalid/invalid/invalid/path")
            self.assertEqual(envs._get_file_from_env("TEST_FILE_VALID", "/default/file"), temp_file.name)
            with self.assertRaises(ValueError):
                envs._get_file_from_env("TEST_FILE_INVALID", "/default/file")
            with self.assertRaises(FileNotFoundError):
                envs._get_file_from_env("TEST_FILE_NOT_EXIST", "/default/file")

    def test_get_ip_address_from_env(self):
        os.environ["TEST_IP_VALID"] = "192.168.1.1"
        os.environ["TEST_IP_INVALID"] = "invalid_ip"
        self.assertEqual(envs._get_ip_address_from_env("TEST_IP_VALID", DEFAULT_IP), "192.168.1.1")
        with self.assertRaises(ValueError):
            envs._get_ip_address_from_env("TEST_IP_INVALID", DEFAULT_IP)
        self.assertEqual(envs._get_ip_address_from_env("TEST_IP_NOT_EXIST", DEFAULT_IP), DEFAULT_IP)

    def test_get_optimization_config(self):
        os.environ["MIS_CONFIG"] = "custom_config"
        self.assertEqual(envs._get_optimization_config(), "custom_config")
        self.assertEqual(envs._get_optimization_config(), "custom_config")

    def test_get_ssl_cert_reqs(self):
        os.environ["MIS_SSL_CERT_REQS"] = "0"
        self.assertEqual(envs._get_ssl_cert_reqs(), 0)
        self.assertEqual(envs._get_ssl_cert_reqs(), 0)


if __name__ == '__main__':
    unittest.main()
