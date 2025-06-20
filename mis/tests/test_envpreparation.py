# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import unittest

import mis.envs as envs
import mis.hub.envpreparation as envpreparation
from mis.args import GlobalArgs


MIS_MODEL = "MindSDK/DeepSeek-R1-Distill-Qwen-1.5B"


class TestEnvPreparation(unittest.TestCase):

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

    def test_enable_envs(self):
        test_envs = {
            "TEST_ENV": "test_value",
            "LD_LIBRARY_PATH": "/path/to/lib",
            "PYTHONPATH": "/path/to/python",
            "PATH": "/path/to/bin",
        }
        envpreparation.enable_envs(test_envs)
        self.assertEqual(os.environ["TEST_ENV"], "test_value")
        self.assertIn("/path/to/lib", os.environ["LD_LIBRARY_PATH"].split(":"))
        self.assertIn("/path/to/python", os.environ["PYTHONPATH"].split(":"))
        self.assertIn("/path/to/bin", os.environ["PATH"].split(":"))

    def test_environment_preparation(self):
        envs.MIS_CACHE_PATH = "/mnt/nfs/data/models"
        args = GlobalArgs()
        args.engine_type = "vllm"
        args.model = MIS_MODEL
        args.served_model_name = None
        args.enable_auto_tools = False
        args.engine_optimization_config = {}

        prepared_args = envpreparation.environment_preparation(args, resolve_env=True)
        self.assertEqual(prepared_args.served_model_name, MIS_MODEL)
        self.assertEqual(prepared_args.tool_parser, "pythonic")
        self.assertEqual(os.environ["VLLM_PLUGINS"], "ascend")
        self.assertEqual(os.environ["VLLM_LOGGING_LEVEL"], envs.MIS_LOG_LEVEL)


if __name__ == '__main__':
    unittest.main()
