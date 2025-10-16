# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import copy
import logging
import unittest
from unittest.mock import patch

import pytest

from mis.llm.entrypoints.openai.api_extensions import MISChatCompletionRequest


class TestAPIExtensions(unittest.TestCase):

    def setUp(self):
        self.valid_params = {
            "frequency_penalty" : 1.5,
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": "Hello"}],
            "min_tokens": 1,
            "model": "Qwen3-8B",
            "presence_penalty": 0.0,
            "seed": 1234,
            "stream": True,
            "temperature": 0.7,
            "top_p": 0.5,
            "max_completion_tokens": 100
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

    def test_init_with_valid_parameters(self):
        """Test initialization with valid parameters."""
        kwargs = copy.deepcopy(self.valid_params)

        request = MISChatCompletionRequest(**kwargs)

        # Check that valid parameters are set
        self.assertEqual(request.frequency_penalty, kwargs["frequency_penalty"])
        self.assertEqual(request.max_tokens, kwargs["max_tokens"])
        self.assertEqual(request.messages, kwargs["messages"])
        self.assertEqual(request.min_tokens, kwargs["min_tokens"])
        self.assertEqual(request.model, kwargs["model"])
        self.assertEqual(request.presence_penalty, kwargs["presence_penalty"])
        self.assertEqual(request.seed, kwargs["seed"])
        self.assertEqual(request.stream, kwargs["stream"])
        self.assertEqual(request.temperature, kwargs["temperature"])
        self.assertEqual(request.top_p, kwargs["top_p"])
        self.assertEqual(request.max_completion_tokens, kwargs["max_completion_tokens"])

    @patch('mis.llm.entrypoints.openai.api_extensions.logger.warning')
    def test_parameter_filtering_and_warnings(self, mock_logger):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["invalid_param"] = "invalid_value"
        request = MISChatCompletionRequest(**kwargs)
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

    def test_no_valid_messages(self):
        test_messages = [
            {"role": "invalid", "content": "test"},
            {"role": "test", "content": "test"}
        ]
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(messages=test_messages)
        assert str(exc_info.value) == "MIS chat completions require at least one valid message"

    def test_frequency_penalty_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["frequency_penalty"] = "1.5"
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for frequency_penalty, expected: float"

    def test_frequency_penalty_less_than_min(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["frequency_penalty"] = -3.0
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for frequency_penalty: -3.0 not in [-2.0, 2.0]"

    def test_frequency_penalty_more_than_max(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["frequency_penalty"] = 2.1
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for frequency_penalty: 2.1 not in [-2.0, 2.0]"

    def test_max_tokens_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["max_tokens"] = "1024"
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for max_tokens, expected: int"

    def test_max_tokens_less_than_min(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["max_tokens"] = 0
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for max_tokens: 0 not in [1, 64000]"

    def test_max_tokens_more_than_max(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["max_tokens"] = 64001
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for max_tokens: 64001 not in [1, 64000]"

    def test_messages_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["messages"] = '[{"role": "user", "content": "Hello"}]'
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Messages must be a list, but get <class 'str'>"

    def test_messages_without(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs.pop("messages")
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Can't find any message in request"

    def test_min_tokens_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["min_tokens"] = "1"
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for min_tokens, expected: int"

    def test_min_tokens_less_than_min(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["min_tokens"] = -1
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for min_tokens: -1 not in [0, 64000]"

    def test_min_tokens_more_than_max(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["min_tokens"] = 64001
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for min_tokens: 64001 not in [0, 64000]"

    def test_model_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["model"] = 1
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for model, expected: str"

    def test_model_invalid_value(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["model"] = "Qwen3-0.6B"
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for model: Qwen3-0.6B not in ('Qwen3-8B',)"

    def test_presence_penalty_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["presence_penalty"] = "0.0"
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for presence_penalty, expected: float"

    def test_presence_penalty_less_than_min(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["presence_penalty"] = -3.0
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for presence_penalty: -3.0 not in [-2.0, 2.0]"

    def test_presence_penalty_more_than_max(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["presence_penalty"] = 2.1
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for presence_penalty: 2.1 not in [-2.0, 2.0]"

    def test_seed_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["seed"] = "1234"
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for seed, expected: int"

    def test_seed_less_than_min(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["seed"] = -9223372036854775809
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for seed: -9223372036854775809 not in [-9223372036854775808, 9223372036854775807]"

    def test_seed_more_than_max(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["seed"] = 9223372036854775809
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for seed: 9223372036854775809 not in [-9223372036854775808, 9223372036854775807]"

    def test_stream_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["stream"] = "True123"
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for stream, expected: bool"

    def test_temperature_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["temperature"] = "0.7"
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for temperature, expected: float"

    def test_temperature_less_than_min(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["temperature"] = -1.0
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for temperature: -1.0 not in [0.0, 2.0]"

    def test_temperature_more_than_max(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["temperature"] = 3.0
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for temperature: 3.0 not in [0.0, 2.0]"

    def test_top_p_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["top_p"] = "0.5"
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for top_p, expected: float"

    def test_top_p_less_than_min(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["top_p"] = 1e-9
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for top_p: 1e-09 not in [1e-08, 1.0]"

    def test_top_p_more_than_max(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["top_p"] = 2.0
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for top_p: 2.0 not in [1e-08, 1.0]"

    def test_max_completion_tokens_invalid_type(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["max_completion_tokens"] = "100"
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Unsupported type for max_completion_tokens, expected: int"

    def test_max_completion_tokens_less_than_min(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["max_completion_tokens"] = 0
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for max_completion_tokens: 0 not in [1, 64000]"

    def test_max_completion_tokens_more_than_max(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["max_completion_tokens"] = 64001
        with pytest.raises(ValueError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for max_completion_tokens: 64001 not in [1, 64000]"

    def test_max_completion_tokens_None(self):
        kwargs = copy.deepcopy(self.valid_params)
        kwargs["max_completion_tokens"] = None
        with pytest.raises(TypeError) as exc_info:
            MISChatCompletionRequest(**kwargs)
        assert str(exc_info.value) == "Invalid value for max_completion_tokens: None"

    def test_model_post_init_with_top_logprobs(self):
        params = {
            "messages": [{"role": "user", "content": "test"}],
            "model": "Qwen3-8B",
            "top_logprobs": 0
        }
        with patch("mis.llm.entrypoints.openai.api_extensions.MISChatCompletionRequest._validate_parameters", return_value=params):
            request = MISChatCompletionRequest(
                messages=self.valid_params["messages"]
            )
            self.assertEqual(request.top_logprobs, None)

    def test_model_post_init_without_top_logprobs(self):
        params = {
            "messages": [{"role": "user", "content": "test"}],
            "model": "Qwen3-8B",
            "top_logprobs": 5,
            "logprobs" : True
        }
        with patch("mis.llm.entrypoints.openai.api_extensions.MISChatCompletionRequest._validate_parameters", return_value=params):
            request = MISChatCompletionRequest(
                messages=self.valid_params["messages"]
            )
            self.assertEqual(request.top_logprobs, 5)

    def _capture_log(self, msg, *args, **kwargs):
        """Capture log messages for testing."""
        self.log_messages.append(msg % args if args else msg)


if __name__ == '__main__':
    unittest.main()
