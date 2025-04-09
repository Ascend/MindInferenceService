# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Request, FastAPI
from pydantic import ValidationError
from starlette.responses import JSONResponse, StreamingResponse
from starlette.datastructures import State
from vllm.entrypoints.openai.api_server import base, chat, models
from vllm.entrypoints.openai.serving_models import BaseModelPath, OpenAIServingModels
from vllm.entrypoints.openai.serving_tokenization import OpenAIServingTokenization
from vllm.entrypoints.openai.protocol import (
    ChatCompletionResponse,
    ChatCompletionStreamResponse,
    ErrorResponse,
)
from vllm.entrypoints.logger import RequestLogger
from vllm.entrypoints.utils import with_cancellation
from vllm.config import ModelConfig

from mis.engine_factory import EngineClient
from mis.llm.entrypoints.openai.api_extensions import (
    MISChatCompletionRequest,
    MISOpenAIServingChat
)
from mis.logger import init_logger
from mis.args import GlobalArgs

logger = init_logger(__name__)

router = APIRouter()

# we only need vLLM /openai/v1/models return `id` `created` `object` `owned_by` `max_model_len`,
# so del `root` `parent` `permission`
MIS_MODEL_REMOVE_FIELDS = [
    "root", "parent", "permission"
]


@router.get("/openai/v1/models")
async def show_available_models(raw_request: Request):
    handler = models(raw_request)

    models_ = await handler.show_available_models()
    for model_ in models_.data:
        for field in MIS_MODEL_REMOVE_FIELDS:
            if hasattr(model_, field):
                delattr(model_, field)

    return JSONResponse(content=models_.model_dump())


def align_non_streaming_response(generator: ChatCompletionResponse):
    """
    remove stop_reason in vllm response to ensure consistent behavior with MindIE-Service
    """
    for choice in generator.choices:
        del choice.stop_reason


async def align_streaming_response(generator: AsyncGenerator[str, None]):
    """
    remove stop_reason in vllm stream response to ensure consistent behavior with MindIE-Service
    """
    async for content in generator:
        if "stop_reason" in content:
            try:
                content_dict = json.loads(content[len("data: "):])
            except json.JSONDecodeError:
                yield content
                continue

            if not isinstance(content_dict, dict):
                yield content
                continue

            try:
                content_obj = ChatCompletionStreamResponse(**content_dict)
            except ValidationError:
                yield content
                continue

            for choice in content_obj.choices:
                del choice.stop_reason

            yield f"data: {content_obj.model_dump_json(exclude_unset=True)}\n\n"
        else:
            yield content


@router.post("/openai/v1/chat/completions")
@with_cancellation
async def create_chat_completions(request: MISChatCompletionRequest,
                                  raw_request: Request):
    handler = chat(raw_request)
    if handler is None:
        return base(raw_request).create_error_response(message="The model does not support Chat Completions API")

    generator = await handler.create_chat_completion(request, raw_request)

    if isinstance(generator, ErrorResponse):
        return JSONResponse(content=generator.model_dump(),
                            status_code=generator.code)

    elif isinstance(generator, ChatCompletionResponse):
        align_non_streaming_response(generator)
        return JSONResponse(content=generator.model_dump())

    generator = align_streaming_response(generator)
    return StreamingResponse(content=generator, media_type="text/event-stream")


async def init_openai_app_state(
        engine_client: EngineClient,
        model_config: ModelConfig,
        state: State,
        args: GlobalArgs
):
    if args.served_model_name is not None:
        served_model_names = [args.served_model_name]
    else:
        served_model_names = [args.model]

    if args.disable_log_requests:
        request_logger = None
    else:
        request_logger = RequestLogger(max_log_len=args.max_log_len)

    base_model_paths = [
        BaseModelPath(name=name, model_path=args.model)
        for name in served_model_names
    ]

    # register openai_serving_models, will be use by function `models`
    state.openai_serving_models = OpenAIServingModels(
        engine_client=engine_client,
        model_config=model_config,
        base_model_paths=base_model_paths,
    )

    # register openai_serving_chat, will be use by function `chat`
    state.openai_serving_chat = MISOpenAIServingChat(
        engine_client,
        model_config,
        state.openai_serving_models,
        "assistant",
        request_logger=request_logger,
        chat_template=None,
        chat_template_content_format="auto"
    )

    # register openai_serving_tokenization, will be use by function `base`
    state.openai_serving_tokenization = OpenAIServingTokenization(
        engine_client,
        model_config,
        state.openai_serving_models,
        request_logger=request_logger,
        chat_template=None,
        chat_template_content_format="auto"
    )

    state.task = model_config.task
