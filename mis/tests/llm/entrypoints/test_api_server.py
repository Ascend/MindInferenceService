# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
import os
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from starlette.datastructures import State
from starlette.responses import JSONResponse

from mis.llm.entrypoints.openai.api_server import (
    create_chat_completions,
    init_openai_app_state,
)


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
        mock_stat.return_value = os.stat_result((0o755, 0, 0, 0, 0, 0, 0, 0, 0, 0))  # Mock a valid stat result

        from mis.args import GlobalArgs
        self.test_args = GlobalArgs(
            model="test_model",
            served_model_name=None,
            disable_log_requests=False,
            max_log_len=1000
        )

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
    def test_create_chat_completions_with_none_handler(self, mock_base, mock_chat):
        """Test create_chat_completions when handler is None."""
        # Setup mocks
        mock_chat.return_value = None
        mock_base_instance = MagicMock()
        from vllm.entrypoints.openai.protocol import ErrorResponse
        mock_error_response = ErrorResponse(message="test error", type="test_type", error="test error", code=400)
        mock_base_instance.create_error_response.return_value = mock_error_response
        mock_base.return_value = mock_base_instance

        mock_request = MagicMock()
        mock_raw_request = MagicMock()

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
        self.assertEqual(response.code, 400)

    @patch('mis.llm.entrypoints.openai.api_server.chat')
    def test_create_chat_completions_with_error_response(self, mock_chat):
        """Test create_chat_completions when handler returns ErrorResponse."""
        # Setup mocks
        mock_handler = AsyncMock()
        from vllm.entrypoints.openai.protocol import ErrorResponse
        mock_error_response = ErrorResponse(message="test error", type="test_type", error="test error", code=404)
        mock_handler.create_chat_completion = AsyncMock(return_value=mock_error_response)
        mock_chat.return_value = mock_handler

        mock_request = MagicMock()
        mock_raw_request = MagicMock()

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
    def test_create_chat_completions_with_chat_response(self, mock_chat):
        """Test create_chat_completions when handler returns ChatCompletionResponse."""
        # Setup mocks
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

        mock_request = MagicMock()
        mock_raw_request = MagicMock()

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
    def test_create_chat_completions_with_streaming_response(self, mock_chat):
        """Test create_chat_completions when handler returns generator."""
        # Setup mocks
        mock_handler = AsyncMock()
        mock_generator = MagicMock()
        mock_handler.create_chat_completion = AsyncMock(return_value=mock_generator)
        mock_chat.return_value = mock_handler

        mock_request = MagicMock()
        mock_raw_request = MagicMock()

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

    def test_init_openai_app_state_with_served_model_name(self):
        """Test init_openai_app_state with served_model_name provided."""
        # Setup
        mock_engine_client = AsyncMock()
        mock_model_config = MagicMock()
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

    def test_init_openai_app_state_without_served_model_name(self):
        """Test init_openai_app_state without served_model_name."""
        # Setup
        mock_engine_client = AsyncMock()
        mock_model_config = MagicMock()
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

    def test_init_openai_app_state_with_disabled_log_requests(self):
        """Test init_openai_app_state with disabled log requests."""
        # Setup
        mock_engine_client = AsyncMock()
        mock_model_config = MagicMock()
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
