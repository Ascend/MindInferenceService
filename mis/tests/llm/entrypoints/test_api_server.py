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
import asyncio
import importlib
import importlib.metadata
import os
import unittest
from unittest.mock import create_autospec, patch, MagicMock, AsyncMock

from fastapi import Request
from packaging import version
from starlette.datastructures import State
from starlette.responses import JSONResponse
from vllm.config import ModelConfig
from vllm.engine.protocol import EngineClient
from mis.llm.entrypoints.openai.api_server import (
    show_available_models,
    create_chat_completions,
    init_openai_app_state,
)


def get_vllm_version():
    try:
        return importlib.metadata.version("vllm")
    except importlib.metadata.PackageNotFoundError:
        return None


class TestApiServer(unittest.TestCase):
    @staticmethod
    def set_up_mock_models():
        # Setup mock data with fields that should be removed
        mock_model_instance = MagicMock()
        mock_model_instance.root = "test_root"
        mock_model_instance.parent = "test_parent"
        mock_model_instance.permission = "test_permission"
        mock_model_instance.id = "test_id"
        mock_model_instance.created = 123456
        mock_model_instance.object = "test_object"
        mock_model_instance.owned_by = "test_owner"
        mock_model_instance.max_model_len = 1024

        # Ensure hasattr returns True for fields to be removed
        mock_model_instance.__dict__.update({
            'root': 'test_root',
            'parent': 'test_parent',
            'permission': 'test_permission',
            'id': 'test_id',
            'created': 123456,
            'object': 'test_object',
            'owned_by': 'test_owner',
            'max_model_len': 1024
        })
        return mock_model_instance

    @patch('os.stat')
    @patch('os.path.isdir')
    def setUp(self, mock_isdir, mock_stat):
        """Set up test fixtures before each test method."""
        mock_isdir.return_value = True
        mock_stat.return_value = os.stat_result((0o750, 0, 0, 0, 0, 0, 0, 0, 0, 0))  # Mock a valid stat result

        from mis.args import GlobalArgs
        self.test_args = GlobalArgs(
            model="test_model",
            served_model_name=None,
            disable_log_requests=False,
            max_log_len=1000
        )

    @patch('mis.llm.entrypoints.openai.api_server.models')
    @patch('os.stat')
    def test_show_available_models(self, mock_stat, mock_models):
        """Test show_available_models endpoint."""
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_response = MagicMock()
        mock_response.data = [self.set_up_mock_models()]
        mock_response.model_dump.return_value = {
            "data": [{
                "id": "test_id",
                "created": 123456,
                "object": "test_object",
                "owned_by": "test_owner",
                "max_model_len": 1024
            }]
        }

        mock_handler = AsyncMock()
        mock_handler.show_available_models = AsyncMock(return_value=mock_response)
        mock_models.return_value = mock_handler

        # Setup request mock
        mock_request = create_autospec(Request)
        mock_request.app.state.request_timeout = 10

        # Create an async function to test
        async def test_show_models():
            response = await show_available_models(mock_request)
            return response

        # Run the async test
        response = self.run_async(test_show_models())

        # Assertions
        mock_models.assert_called_once_with(mock_request)
        mock_handler.show_available_models.assert_awaited_once()

        # Check that the response is a JSONResponse
        self.assertIsInstance(response, JSONResponse)

        # Check that removed fields are not in the response
        response_data = response.body
        self.api_assert_models(response_data)

    def api_assert_models(self, response_data):
        self.assertNotIn(b"root", response_data)
        self.assertNotIn(b"parent", response_data)
        self.assertNotIn(b"permission", response_data)

        # Check that required fields are in the response
        self.assertIn(b"id", response_data)
        self.assertIn(b"created", response_data)
        self.assertIn(b"object", response_data)
        self.assertIn(b"owned_by", response_data)
        self.assertIn(b"max_model_len", response_data)

    @patch('mis.llm.entrypoints.openai.api_server.chat')
    @patch('mis.llm.entrypoints.openai.api_server.base')
    @patch('os.stat')
    def test_create_chat_completions_with_none_handler(self, mock_stat, mock_base, mock_chat):
        """Test create_chat_completions when handler is None."""
        # Setup mocks
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_chat.return_value = None
        mock_base_instance = MagicMock()
        from vllm.entrypoints.openai.protocol import ErrorResponse
        vllm_version = get_vllm_version()
        if vllm_version is None:
            raise Exception("vLLM package is not installed.")
        elif version.parse(vllm_version) > version.parse("0.10.0"):
            from vllm.entrypoints.openai.protocol import ErrorInfo
            mock_error_response = ErrorResponse(error=ErrorInfo(
                message="test error", type="test_type", error="test error", code=400
            ))
        else:
            mock_error_response = ErrorResponse(message="test error", type="test_type", error="test error", code=400)
        mock_base_instance.create_error_response.return_value = mock_error_response
        mock_base.return_value = mock_base_instance

        mock_request = create_autospec(Request)
        mock_raw_request = create_autospec(Request)

        mock_raw_request.app = create_autospec(object)
        mock_raw_request.app.state = create_autospec(object)
        mock_raw_request.app.state.request_timeout = 10

        # Create an async function to test
        async def test_create_chat():
            response = await create_chat_completions(mock_request, mock_raw_request)
            return response

        # Run the async test
        response = self.run_async(test_create_chat())

        # Assertions
        mock_chat.assert_called_once_with(mock_raw_request)
        mock_base.assert_called_once_with(mock_raw_request)
        mock_base_instance.create_error_response.assert_called_once_with(
            message="The model does not support Chat Completions API"
        )
        self.assertIsInstance(response, ErrorResponse)
        vllm_version = get_vllm_version()
        if version.parse(vllm_version) > version.parse("0.10.0"):
            self.assertEqual(response.error.code, 400)
        else:
            self.assertEqual(response.code, 400)


    @patch('mis.llm.entrypoints.openai.api_server.chat')
    @patch('os.stat')
    def test_create_chat_completions_with_error_response(self, mock_stat, mock_chat):
        """Test create_chat_completions when handler returns ErrorResponse."""
        # Setup mocks
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_handler = AsyncMock()
        from vllm.entrypoints.openai.protocol import ErrorResponse
        vllm_version = get_vllm_version()
        if vllm_version is None:
            raise Exception("vLLM package is not installed.")
        elif version.parse(vllm_version) > version.parse("0.10.0"):
            from vllm.entrypoints.openai.protocol import ErrorInfo
            mock_error_response = ErrorResponse(error=ErrorInfo(
                message="test error", type="test_type", error="test error", code=404
            ))
        else:
            mock_error_response = ErrorResponse(message="test error", type="test_type", error="test error", code=404)
        mock_handler.create_chat_completion = AsyncMock(return_value=mock_error_response)
        mock_chat.return_value = mock_handler

        mock_request = create_autospec(Request)
        mock_raw_request = create_autospec(Request)

        mock_raw_request.app = create_autospec(object)
        mock_raw_request.app.state = create_autospec(object)
        mock_raw_request.app.state.request_timeout = 10

        # Create an async function to test
        async def test_create_chat():
            response = await create_chat_completions(mock_request, mock_raw_request)
            return response

        # Run the async test
        response = self.run_async(test_create_chat())

        # Assertions
        self.assertIsInstance(response, JSONResponse)
        self.assertEqual(response.status_code, 404)
        mock_chat.assert_called_once_with(mock_raw_request)
        mock_handler.create_chat_completion.assert_awaited_once()

    @patch('mis.llm.entrypoints.openai.api_server.chat')
    @patch('os.stat')
    def test_create_chat_completions_with_chat_response(self, mock_stat, mock_chat):
        """Test create_chat_completions when handler returns ChatCompletionResponse."""
        # Setup mocks
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_handler = AsyncMock()
        from vllm.entrypoints.openai.protocol import ChatCompletionResponse
        mock_chat_response = ChatCompletionResponse(
            id="test_id",
            choices=[],
            created=123456,
            model="test_model",
            object="chat.completion",
            usage={}
        )
        mock_handler.create_chat_completion = AsyncMock(return_value=mock_chat_response)
        mock_chat.return_value = mock_handler

        mock_request = create_autospec(Request)
        mock_raw_request = create_autospec(Request)

        mock_raw_request.app = create_autospec(object)
        mock_raw_request.app.state = create_autospec(object)
        mock_raw_request.app.state.request_timeout = 10

        # Create an async function to test
        async def test_create_chat():
            response = await create_chat_completions(mock_request, mock_raw_request)
            return response

        # Run the async test
        response = self.run_async(test_create_chat())

        # Assertions
        self.assertIsInstance(response, JSONResponse)
        mock_chat.assert_called_once_with(mock_raw_request)
        mock_handler.create_chat_completion.assert_awaited_once()

    @patch('mis.llm.entrypoints.openai.api_server.chat')
    @patch('os.stat')
    def test_create_chat_completions_with_streaming_response(self, mock_stat, mock_chat):
        """Test create_chat_completions when handler returns generator."""
        # Setup mocks
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_handler = AsyncMock()
        mock_generator = MagicMock()
        mock_handler.create_chat_completion = AsyncMock(return_value=mock_generator)
        mock_chat.return_value = mock_handler

        mock_request = create_autospec(Request)
        mock_raw_request = create_autospec(Request)

        mock_raw_request.app = create_autospec(object)
        mock_raw_request.app.state = create_autospec(object)
        mock_raw_request.app.state.request_timeout = 10

        # Create an async function to test
        async def test_create_chat():
            response = await create_chat_completions(mock_request, mock_raw_request)
            return response

        # Run the async test
        response = self.run_async(test_create_chat())

        # Assertions
        from starlette.responses import StreamingResponse
        self.assertIsInstance(response, StreamingResponse)
        self.assertEqual(response.media_type, "text/event-stream")
        mock_chat.assert_called_once_with(mock_raw_request)
        mock_handler.create_chat_completion.assert_awaited_once()

    @patch('os.stat')
    def test_init_openai_app_state_with_served_model_name(self, mock_stat):
        """Test init_openai_app_state with served_model_name provided."""
        # Setup
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_engine_client = AsyncMock(spec=EngineClient)
        mock_model_config = MagicMock(spec=ModelConfig)
        mock_model_config.task = "test_task"
        mock_state = State()
        from mis.args import GlobalArgs
        args = GlobalArgs(
            model="test_model",
            served_model_name="custom_model_name",
            disable_log_requests=False,
            max_log_len=1000
        )

        # Create an async function to test
        async def test_init_state():
            await init_openai_app_state(mock_engine_client, mock_model_config, mock_state, args)

        # Run the async test
        self.run_async(test_init_state())

        # Assertions
        self.assertEqual(mock_state.task, "test_task")
        self.assertIsNotNone(mock_state.openai_serving_models)
        self.assertIsNotNone(mock_state.openai_serving_chat)
        self.assertIsNotNone(mock_state.openai_serving_tokenization)

    @patch('os.stat')
    def test_init_openai_app_state_without_served_model_name(self, mock_stat):
        """Test init_openai_app_state without served_model_name."""
        # Setup
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_engine_client = AsyncMock(spec=EngineClient)
        mock_model_config = MagicMock(spec=ModelConfig)
        mock_model_config.task = "test_task"
        mock_state = State()
        from mis.args import GlobalArgs
        args = GlobalArgs(
            model="test_model",
            served_model_name=None,
            disable_log_requests=False,
            max_log_len=1000
        )

        # Create an async function to test
        async def test_init_state():
            await init_openai_app_state(mock_engine_client, mock_model_config, mock_state, args)

        # Run the async test
        self.run_async(test_init_state())

        # Assertions
        self.assertEqual(mock_state.task, "test_task")
        self.assertIsNotNone(mock_state.openai_serving_models)
        self.assertIsNotNone(mock_state.openai_serving_chat)
        self.assertIsNotNone(mock_state.openai_serving_tokenization)

    @patch('os.stat')
    def test_init_openai_app_state_with_disabled_log_requests(self, mock_stat):
        """Test init_openai_app_state with disabled log requests."""
        # Setup
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_engine_client = AsyncMock(spec=EngineClient)
        mock_model_config = MagicMock(spec=ModelConfig)
        mock_model_config.task = "test_task"
        mock_state = State()
        from mis.args import GlobalArgs
        args = GlobalArgs(
            model="test_model",
            served_model_name=None,
            disable_log_requests=True,
            max_log_len=1000
        )

        # Create an async function to test
        async def test_init_state():
            await init_openai_app_state(mock_engine_client, mock_model_config, mock_state, args)

        # Run the async test
        self.run_async(test_init_state())

        # Assertions
        self.assertEqual(mock_state.task, "test_task")
        self.assertIsNotNone(mock_state.openai_serving_models)
        self.assertIsNotNone(mock_state.openai_serving_chat)
        self.assertIsNotNone(mock_state.openai_serving_tokenization)

    @patch('os.stat')
    def test_init_openai_app_state_with_engine_client_is_invalid(self, mock_stat):
        """Test init_openai_app_state with engine client is invalid."""
        # Setup
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_model_config = MagicMock(spec=ModelConfig)
        mock_model_config.task = "test_task"
        mock_state = State()
        from mis.args import GlobalArgs
        args = GlobalArgs(
            model="test_model",
            served_model_name=None,
            disable_log_requests=True,
            max_log_len=1000
        )

        # Create an async function to test
        async def test_init_state():
            await init_openai_app_state("invalid_type", mock_model_config, mock_state, args)

        # Run the async test
        with self.assertRaises(TypeError) as context:
            self.run_async(test_init_state())

    @patch('os.stat')
    def test_init_openai_app_state_with_model_config_is_invalid(self, mock_stat):
        """Test init_openai_app_state with engine client is invalid."""
        # Setup
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_engine_client = AsyncMock(spec=EngineClient)
        mock_state = State()
        from mis.args import GlobalArgs
        args = GlobalArgs(
            model="test_model",
            served_model_name=None,
            disable_log_requests=True,
            max_log_len=1000
        )

        # Create an async function to test
        async def test_init_state():
            await init_openai_app_state(mock_engine_client, "invalid_type", mock_state, args)

        # Run the async test
        with self.assertRaises(TypeError) as context:
            self.run_async(test_init_state())

    @patch('os.stat')
    def test_init_openai_app_state_with_state_is_invalid(self, mock_stat):
        """Test init_openai_app_state with engine client is invalid."""
        # Setup
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_engine_client = AsyncMock(spec=EngineClient)
        mock_model_config = MagicMock(spec=ModelConfig)
        mock_model_config.task = "test_task"
        from mis.args import GlobalArgs
        args = GlobalArgs(
            model="test_model",
            served_model_name=None,
            disable_log_requests=True,
            max_log_len=1000
        )

        # Create an async function to test
        async def test_init_state():
            await init_openai_app_state(mock_engine_client, mock_model_config, "invalid_type", args)

        # Run the async test
        with self.assertRaises(TypeError) as context:
            self.run_async(test_init_state())

    @patch('os.stat')
    def test_init_openai_app_state_with_args_is_invalid(self, mock_stat):
        """Test init_openai_app_state with engine client is invalid."""
        # Setup
        mock_stat.return_value = MagicMock(st_uid=1000, st_gid=1000, st_mode=0o600)
        mock_engine_client = AsyncMock(spec=EngineClient)
        mock_model_config = MagicMock(spec=ModelConfig)
        mock_model_config.task = "test_task"
        mock_state = State()

        # Create an async function to test
        async def test_init_state():
            await init_openai_app_state(mock_engine_client, mock_model_config, mock_state, "invalid_type")

        # Run the async test
        with self.assertRaises(TypeError) as context:
            self.run_async(test_init_state())

    def run_async(self, coroutine):
        """Helper method to run async tests avoiding event loop issues."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            task = loop.create_task(coroutine)
            return task
        else:
            return asyncio.run(coroutine)


if __name__ == '__main__':
    unittest.main()
