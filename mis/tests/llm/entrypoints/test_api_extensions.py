import unittest
from unittest.mock import patch

from mis.llm.entrypoints.openai.api_extensions import MISChatCompletionRequest


class TestAPIExtensions(unittest.TestCase):

    def setUp(self):
        self.valid_params = {
            "messages": [{"role": "user", "content": "test"}],
            "model": "test_model",
            "invalid_param": "invalid_value"
        }

    @patch('mis.llm.entrypoints.openai.api_extensions.logger.warning')
    def test_parameter_filtering_and_warnings(self, mock_logger):
        request = MISChatCompletionRequest(**self.valid_params)
        self.assertIn("messages", request.__dict__)
        self.assertIn("model", request.__dict__)
        self.assertNotIn("invalid_param", request.__dict__)
        mock_logger.assert_called_once_with("MIS chat completion ignore param `invalid_param`.")

    def test_message_cleaning(self):
        test_messages = [
            {"role": "user", "content": "test"},
            {"role": "tool", "content": "test"},
            {"role": "invalid", "content": "test"},
            {"role": "assistant", "content": "test"}
        ]
        request = MISChatCompletionRequest(messages=test_messages)
        self.assertEqual(len(request.messages), 3)
        roles = [msg["role"] for msg in request.messages]
        self.assertIn("user", roles)
        self.assertIn("tool", roles)
        self.assertIn("assistant", roles)
        self.assertNotIn("invalid", roles)

    def test_default_field_settings(self):
        request = MISChatCompletionRequest(
            messages=self.valid_params["messages"],
            stream=True,
            stream_options={"continuous_usage_stats": True},
            tools=[{
                "type": "function",
                "function": {
                    "name": "get_forecast", "description": "Get the weather forecast for a given location",
                    "parameters":
                        {"type": "object","properties":
                            {"city":
                                 {"type": "string",
                                  "description": "The city to get the forecast for, e.g. 'New York'"},
                             "state": {"type": "string",
                                       "description": "The two-letter abbreviation for the state, e.g. 'NY'"},
                             "days": {"type": "integer", "description": "Number of days to get the forecast for (1-7)"},
                             "unit": {"type": "string", "description": "The unit to fetch the temperature in",
                                      "enum": ["celsius", "fahrenheit"]}
                             },
                         "required": ["city", "state", "days", "unit"]}}
            }],
            tool_choice="required",
        )
        self.assertEqual(request.stream_options.continuous_usage_stats, None)

    def test_model_post_init(self):
        request = MISChatCompletionRequest(
            messages=self.valid_params["messages"],
            top_logprobs=0
        )
        self.assertEqual(request.top_logprobs, None)


if __name__ == '__main__':
    unittest.main()
