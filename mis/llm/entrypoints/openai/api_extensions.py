# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from typing import Any, ClassVar

from vllm.entrypoints.openai.protocol import ChatCompletionRequest
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat

from mis.logger import init_logger

logger = init_logger(__name__)

# MIS chat completion supported fields
MIS_CHAT_COMPLETION_WHITELIST = {
    # openai params
    "messages",
    "model",
    "frequency_penalty",
    "max_tokens",
    "presence_penalty",
    "seed",
    "stop",
    "stream",
    "stream_options",
    "temperature",
    "top_p",

    # tools call
    "tools",
    "tool_choice",

    # vLLM params
    "top_k",
}


class MISChatCompletionRequest(ChatCompletionRequest):
    model_post_init: ClassVar[Any]

    def __init__(self, **kwargs):
        used_kwargs = {}
        for key in kwargs:
            if key in MIS_CHAT_COMPLETION_WHITELIST:
                used_kwargs[key] = kwargs[key]
            else:
                logger.warning(f"MIS chat completion ignore param `{key}`.")
        self.remove_invalid_messages(used_kwargs)
        self.set_default_field(used_kwargs)
        super().__init__(**used_kwargs)

    @staticmethod
    def remove_invalid_messages(kwargs):
        """
        MindIE-Service only accept role in [system, assistant, user, tool]
        """
        roles = ["system", "assistant", "user", "tool"]
        if "messages" not in kwargs or not isinstance(kwargs["messages"], list):
            return
        new_messages = []
        for message in kwargs["messages"]:
            if not isinstance(message, dict):
                continue
            if "role" in message and message["role"] in roles:
                new_messages.append(message)
            else:
                logger.warning("MIS chat completions only accept role in [system, assistant, user, tool]")
        kwargs["messages"] = new_messages

    @staticmethod
    def set_default_field(kwargs):
        if "stream_options" in kwargs and \
                isinstance(kwargs["stream_options"], dict) and "continuous_usage_stats" in kwargs["stream_options"]:
            logger.warning("MIS chat completions ignore stream_options.continuous_usage_stats")
            kwargs["stream_options"]["continuous_usage_stats"] = None

    def model_post_init(self, __context: Any) -> None:
        if getattr(self, "top_logprobs", None) == 0:
            setattr(self, "top_logprobs", None)


class MISOpenAIServingMixin:
    pass


class MISOpenAIServingChat(MISOpenAIServingMixin, OpenAIServingChat):
    pass
