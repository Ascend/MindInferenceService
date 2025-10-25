#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

from mis.llm.entrypoints.launcher import _build_engine_client_from_args, _build_app, _init_app_state, _run_server


class TestLauncher(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        from mis.args import GlobalArgs
        self.test_args = GlobalArgs(
            model="test_model",
            engine_type="vllm",
            host="127.0.0.1",
            port=8000,
        )

    @patch('mis.llm.entrypoints.launcher.AutoEngine.from_config')
    def test_build_engine_client_from_args(self, mock_from_config):
        """Test build_engine_client_from_args async context manager."""
        # Setup mock
        mock_engine_client = MagicMock()
        mock_from_config.return_value = mock_engine_client

        # Create an async function to test the context manager
        async def test_context_manager():
            async with _build_engine_client_from_args(self.test_args) as engine_client:
                return engine_client

        # Run the async test
        engine_client = self.run_async(test_context_manager())

        # Assertions
        mock_from_config.assert_called_once_with(self.test_args)
        self.assertEqual(engine_client, mock_engine_client)

    @patch('mis.llm.entrypoints.launcher.AutoEngine.from_config')
    def test_build_engine_client_from_args_with_shutdown(self, mock_from_config):
        """Test build_engine_client_from_args properly calls shutdown."""
        # Setup mock
        mock_engine_client = MagicMock()
        mock_engine_client.shutdown = MagicMock()
        mock_from_config.return_value = mock_engine_client

        # Create an async function to test the context manager
        async def test_context_manager():
            async with _build_engine_client_from_args(self.test_args) as engine_client:
                pass  # Just enter and exit context

        # Run the async test
        self.run_async(test_context_manager())

        # Assertions
        mock_from_config.assert_called_once_with(self.test_args)
        mock_engine_client.shutdown.assert_called_once()

    @patch('mis.llm.entrypoints.openai.api_server.init_openai_app_state')
    def test_init_app_state_vllm(self, mock_init_openai_app_state):
        """Test init_app_state function with vllm engine."""
        # Setup mocks
        mock_engine_client = AsyncMock()
        mock_model_config = MagicMock()
        mock_app = MagicMock()

        # Create an async function to test
        async def test_init_app_state():
            await _init_app_state(mock_engine_client, mock_model_config, mock_app, self.test_args)

        # Run the async test
        self.run_async(test_init_app_state())

        # Assertions
        mock_init_openai_app_state.assert_called_once_with(
            mock_engine_client, mock_model_config, mock_app.state, self.test_args)

    def test_init_app_state_invalid_engine(self):
        """Test init_app_state function with invalid engine type."""
        # Setup
        mock_engine_client = AsyncMock()
        mock_model_config = MagicMock()
        mock_app = MagicMock()
        from mis.args import GlobalArgs
        invalid_args = GlobalArgs(engine_type="invalid_engine")

        # Create an async function to test
        async def test_init_app_state():
            await _init_app_state(mock_engine_client, mock_model_config, mock_app, invalid_args)

        # Assertions
        with self.assertRaises(ValueError) as context:
            self.run_async(test_init_app_state())

        self.assertIn("Available EngineType is in ('vllm',)", str(context.exception))

    @patch('mis.llm.entrypoints.launcher.serve_http')
    @patch('mis.llm.entrypoints.launcher.create_server_socket')
    @patch('mis.llm.entrypoints.launcher.set_ulimit')
    @patch('mis.llm.entrypoints.launcher.AutoEngine.from_config')
    @patch('mis.llm.entrypoints.openai.api_server.init_openai_app_state')
    def test_run_server(self, mock_init_openai_app_state, mock_from_config, mock_set_ulimit,
                        mock_create_server_socket, mock_serve_http):
        """Test run_server function."""
        # Setup mocks
        mock_engine_client = AsyncMock()
        mock_engine_client.get_model_config = AsyncMock(return_value=MagicMock())
        mock_engine_client.shutdown = MagicMock()

        mock_from_config.return_value = mock_engine_client

        mock_socket = MagicMock()
        mock_create_server_socket.return_value = mock_socket

        # Create a coroutine for the shutdown_task
        async def mock_shutdown():
            return MagicMock()

        mock_serve_http.return_value = mock_shutdown()

        # Create an async function to test
        async def test_run_server():
            await _run_server(self.test_args)

        # Run the async test
        self.run_async(test_run_server())

        # Assertions
        mock_set_ulimit.assert_called_once()
        mock_from_config.assert_called_once_with(self.test_args)
        mock_create_server_socket.assert_called_once()
        mock_engine_client.get_model_config.assert_awaited_once()
        mock_serve_http.assert_called_once()
        mock_socket.close.assert_called_once()

    def run_async(self, coroutine):
        """Helper method to run async tests avoiding event loop issues."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If there's a running loop, create a task
            task = loop.create_task(coroutine)
            # In a test environment, we might need to handle this differently
            return task
        else:
            # Otherwise, use asyncio.run()
            return asyncio.run(coroutine)


if __name__ == '__main__':
    unittest.main()
