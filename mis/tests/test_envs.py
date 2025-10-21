# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import mis.envs as envs
from mis import constants

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
        self.assertTrue(envs._get_bool_from_env("TEST_BOOL_TRUE", False))
        self.assertFalse(envs._get_bool_from_env("TEST_BOOL_FALSE", True))
        self.assertFalse(envs._get_bool_from_env("TEST_BOOL_NOT_EXIST", False))

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
            envs._get_str_from_env("TEST_STR_INVALID", "default", ("valid_value",))
        self.assertEqual(envs._get_str_from_env("TEST_STR_NOT_EXIST", "default"), "default")

    @patch('os.getuid', return_value=1000)
    @patch('os.stat')
    def test_get_cache_path_from_env(self, mock_stat, mock_getuid):
        mock_stat_result = MagicMock()
        mock_stat_result.st_mode = 0o040755
        mock_stat_result.st_uid = 1000
        mock_stat.return_value = mock_stat_result

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

    def test_get_optimization_config(self):
        os.environ["MIS_CONFIG"] = "atlas800ia2-1x32gb-bf16-vllm-default"
        self.assertEqual(envs._get_str_from_env("MIS_CONFIG", None, constants.MIS_CONFIGS_LIST),
                         "atlas800ia2-1x32gb-bf16-vllm-default")


if __name__ == '__main__':
    unittest.main()
