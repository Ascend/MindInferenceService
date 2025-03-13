# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
from vllm.entrypoints.openai.protocol import ChatCompletionRequest
from vllm.entrypoints.openai.serving_chat import OpenAIServingChat

from mis.logger import init_logger

logger = init_logger(__name__)

# MIS chat completion supported fields
MIS_CHAT_COMPLETION_WHITELIST = [
    # openai params
    "messages",
    "model",
    "frequency_penalty",
    "logit_bias",
    "logprobs",
    "top_logprobs",
    "max_tokens",
    "max_completion_tokens",
    "n",
    "presence_penalty",
    "seed",
    "stop",
    "stream",
    "stream_options",
    "temperature",
    "top_p",
    # vLLM params
    "top_k",
]


class MISChatCompletionRequest(ChatCompletionRequest):

    def __init__(self, **kwargs):
        used_kwargs = {}
        for key in kwargs:
            if key in MIS_CHAT_COMPLETION_WHITELIST:
                used_kwargs[key] = kwargs[key]
            else:
                logger.warning(f"MIS chat completion ignore param `{key}`.")
        super().__init__(**used_kwargs)


class MISOpenAIServingMixin:
    pass


class MISOpenAIServingChat(MISOpenAIServingMixin, OpenAIServingChat):
    pass
