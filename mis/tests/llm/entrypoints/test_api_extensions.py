# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import logging
import unittest
from unittest.mock import patch

from mis.llm.entrypoints.openai.api_extensions import MISChatCompletionRequest


class TestAPIExtensions(unittest.TestCase):

    def setUp(self):
        self.valid_params = {
            "messages": [{"role": "user", "content": "test"}],
            "model": "MindSDK/DeepSeek-R1-Distill-Qwen-7B",
            "invalid_param": "invalid_value"
        }
        # Capture logs during testing
        self.log_messages = []
        self.logger = logging.getLogger('mis.llm.entrypoints.openai.api_extensions')

        # Mock the logger to capture warning messages
        self.original_warning = self.logger.warning
        self.logger.warning = self._capture_log

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original logger
        self.logger.warning = self.original_warning
        self.log_messages = []

    @patch('mis.llm.entrypoints.openai.api_extensions.logger.warning')
    def test_parameter_filtering_and_warnings(self, mock_logger):
        request = MISChatCompletionRequest(**self.valid_params)
        self.assertIn("messages", request.__dict__)
        self.assertIn("model", request.__dict__)
        self.assertNotIn("invalid_param", request.__dict__)
        mock_logger.assert_called_once_with("MIS chat completion ignore invalid param.")

    def test_message_cleaning(self):
        test_messages = [
            {"role": "user", "content": "test"},
            {"role": "invalid", "content": "test"},
            {"role": "assistant", "content": "test"}
        ]
        request = MISChatCompletionRequest(messages=test_messages)
        self.assertEqual(len(request.messages), len(test_messages) - 1)
        roles = [msg["role"] for msg in request.messages]
        self.assertIn("user", roles)
        self.assertIn("assistant", roles)
        self.assertNotIn("invalid", roles)

    def test_model_post_init(self):
        request = MISChatCompletionRequest(
            messages=self.valid_params["messages"],
            top_logprobs=0
        )
        self.assertEqual(request.top_logprobs, None)

    def test_init_with_valid_parameters(self):
        """Test initialization with valid parameters."""
        kwargs = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "MindSDK/DeepSeek-R1-Distill-Qwen-7B",
            "temperature": 0.7,
            "max_completion_tokens": 100,
            "stream": True
        }

        request = MISChatCompletionRequest(**kwargs)

        # Check that valid parameters are set
        self.assertEqual(request.messages, kwargs["messages"])
        self.assertEqual(request.model, kwargs["model"])
        self.assertEqual(request.temperature, kwargs["temperature"])
        self.assertEqual(request.max_completion_tokens, kwargs["max_completion_tokens"])
        self.assertEqual(request.stream, kwargs["stream"])

    def test_init_with_unsupported_parameters(self):
        """Test initialization with unsupported parameters."""
        kwargs = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "MindSDK/DeepSeek-R1-Distill-Qwen-7B",
            "unsupported_param": "value",
            "another_unsupported": 123
        }

        request = MISChatCompletionRequest(**kwargs)

        # Check that valid parameters are set
        self.assertEqual(request.messages, kwargs["messages"])
        self.assertEqual(request.model, kwargs["model"])

        # Check that unsupported parameters are ignored with warning logs
        self.assertIn("MIS chat completion ignore invalid param.", self.log_messages)

    def test_parameter_validation_with_valid_values(self):
        """Test parameter validation with valid values."""
        kwargs = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "MindSDK/DeepSeek-R1-Distill-Qwen-7B",
            "temperature": 1.5,
            "frequency_penalty": 0.5,
            "presence_penalty": -1.2,
            "top_p": 0.9,
            "stream": False
        }

        request = MISChatCompletionRequest(**kwargs)

        # Check that values are properly converted and set
        self.assertEqual(request.temperature, 1.5)
        self.assertEqual(request.frequency_penalty, 0.5)
        self.assertEqual(request.presence_penalty, -1.2)
        self.assertEqual(request.top_p, 0.9)
        self.assertFalse(request.stream)

    def test_parameter_validation_with_type_errors(self):
        """Test parameter validation with type errors."""
        kwargs = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "MindSDK/DeepSeek-R1-Distill-Qwen-7B",
            "max_completion_tokens": "150",
            "temperature": "0.8",
        }

        request = MISChatCompletionRequest(**kwargs)

        self.assertEqual(request.max_completion_tokens, None)
        self.assertEqual(request.temperature, None)

    def _capture_log(self, msg, *args, **kwargs):
        """Capture log messages for testing."""
        self.log_messages.append(msg % args if args else msg)


if __name__ == '__main__':
    unittest.main()
