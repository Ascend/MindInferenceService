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
import unittest
from unittest.mock import patch, MagicMock

from mis import constants
from mis.args import GlobalArgs
from mis.llm.engine_factory import AutoEngine, VLLMEngine


class TestAutoEngine(unittest.TestCase):
    def test_from_config_with_none_args(self):
        with self.assertRaises(TypeError) as context:
            VLLMEngine.from_args(None)
        self.assertEqual(str(context.exception), "Invalid args type: <class 'NoneType'>, GlobalArgs needed")

    def test_from_config_with_invalid_args_type(self):
        invalid_args = "not a GlobalArgs instance"
        with self.assertRaises(TypeError) as context:
            VLLMEngine.from_args(invalid_args)
        self.assertEqual(str(context.exception), "Invalid args type: <class 'str'>, GlobalArgs needed")

    @patch('mis.llm.engine_factory.VLLMEngine.from_args')
    def test_from_config_vllm(self, mock_from_args):
        # Mock a GlobalArgs instance
        args = GlobalArgs()
        args.engine_type = "vllm"
        args.model = "test_model"
        args.served_model_name = "test_served_model_name"
        args.disable_log_stats = False
        args.disable_log_requests = False
        args.engine_optimization_config = {}

        # Mock the return value of VLLMEngine.from_args
        mock_from_args.return_value = MagicMock()

        # Call the from_config method
        result = AutoEngine.from_config(args)

        # Verify that VLLMEngine.from_args was called correctly
        mock_from_args.assert_called_once_with(args)
        self.assertIsInstance(result, MagicMock)

    def test_from_config_invalid_engine_type(self):
        # Mock a GlobalArgs instance
        args = GlobalArgs()
        args.engine_type = "invalid_engine_type"

        # Call the from_config method, expecting a NotImplementedError
        with self.assertRaises(NotImplementedError) as context:
            AutoEngine.from_config(args)

        # Verify the exception message
        self.assertEqual(str(context.exception), "Model Engine for 'invalid_engine_type' is not implemented, "
                                                 f"available types are {constants.MIS_ENGINE_TYPES}.")


class TestVLLMEngine(unittest.TestCase):
    def test_from_config_with_none_args(self):
        with self.assertRaises(TypeError) as context:
            result = VLLMEngine.from_args(None)
        self.assertEqual(str(context.exception), "Invalid args type: <class 'NoneType'>, GlobalArgs needed")

    def test_from_config_with_invalid_args_type(self):
        invalid_args = "not a GlobalArgs instance"
        with self.assertRaises(TypeError) as context:
            result = VLLMEngine.from_args(invalid_args)
        self.assertEqual(str(context.exception), "Invalid args type: <class 'str'>, GlobalArgs needed")


    @patch('vllm.engine.arg_utils.AsyncEngineArgs')
    @patch('vllm.engine.async_llm_engine.AsyncLLMEngine.from_engine_args')
    def test_from_args(self, mock_from_engine_args, mock_async_engine_args):
        # Mock a GlobalArgs instance
        args = GlobalArgs()
        args.model = "test_model"
        args.served_model_name = "test_served_model_name"
        args.disable_log_stats = False
        args.disable_log_requests = False
        args.engine_optimization_config = {}

        # Mock the return values of AsyncEngineArgs and AsyncLLMEngine.from_engine_args
        mock_async_engine_args.return_value = MagicMock()
        mock_from_engine_args.return_value = MagicMock()

        # Call the from_args method
        result = VLLMEngine.from_args(args)

        # Verify that AsyncEngineArgs was called correctly
        mock_async_engine_args.assert_called_once_with(
            model=args.model,
            served_model_name=args.served_model_name,
            disable_log_stats=args.disable_log_stats,
            load_format='safetensors',
            disable_log_requests=args.disable_log_requests,
            **args.engine_optimization_config
        )

        # Verify that AsyncLLMEngine.from_engine_args was called correctly
        mock_from_engine_args.assert_called_once_with(mock_async_engine_args.return_value)
        self.assertIsInstance(result, MagicMock)

    @patch('vllm.engine.arg_utils.AsyncEngineArgs')
    def test_from_args_import_error(self, mock_async_engine_args):
        # Mock a GlobalArgs instance
        args = GlobalArgs()
        args.model = "test_model"
        args.served_model_name = "test_served_model_name"
        args.disable_log_stats = False
        args.disable_log_requests = False
        args.engine_optimization_config = {}

        # Simulate an import failure for AsyncEngineArgs
        mock_async_engine_args.side_effect = ImportError("Failed to import AsyncEngineArgs")

        # Call the from_args method, expecting an ImportError
        with self.assertRaises(Exception) as context:
            VLLMEngine.from_args(args)

        # Verify the exception message
        self.assertEqual(str(context.exception), "Failed to initialize AsyncLLMEngine: "
                                                 "Failed to import AsyncEngineArgs")

    @patch('vllm.engine.arg_utils.AsyncEngineArgs')
    @patch('vllm.engine.async_llm_engine.AsyncLLMEngine.from_engine_args')
    def test_from_args_initialization_error(self, mock_from_engine_args, mock_async_engine_args):
        # Mock a GlobalArgs instance
        args = GlobalArgs()
        args.model = "test_model"
        args.served_model_name = "test_served_model_name"
        args.disable_log_stats = False
        args.disable_log_requests = False
        args.engine_optimization_config = {}

        # Mock the return values of AsyncEngineArgs and AsyncLLMEngine.from_engine_args
        mock_async_engine_args.return_value = MagicMock()
        mock_from_engine_args.side_effect = Exception("Failed to initialize AsyncLLMEngine")

        # Call the from_args method, expecting an Exception
        with self.assertRaises(Exception) as context:
            VLLMEngine.from_args(args)

        # Verify the exception message
        self.assertEqual(str(context.exception), "Failed to initialize AsyncLLMEngine: "
                                                 "Failed to initialize AsyncLLMEngine")


if __name__ == '__main__':
    unittest.main()