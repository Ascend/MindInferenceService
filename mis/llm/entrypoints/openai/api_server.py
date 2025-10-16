# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
from http import HTTPStatus
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Request
from pydantic import ValidationError
from starlette.datastructures import State
from starlette.responses import JSONResponse, StreamingResponse
from vllm.config import ModelConfig
from vllm.engine.protocol import EngineClient
from vllm.entrypoints.logger import RequestLogger
from vllm.entrypoints.openai.api_server import base, chat, models
from vllm.entrypoints.openai.protocol import (
    ChatCompletionResponse,
    ChatCompletionStreamResponse,
    ErrorResponse,
)
from vllm.entrypoints.openai.serving_models import BaseModelPath, OpenAIServingModels
from vllm.entrypoints.openai.serving_tokenization import OpenAIServingTokenization

from mis.args import GlobalArgs
from mis.constants import REQUEST_TIMEOUT_IN_SEC
from mis.llm.entrypoints.openai.api_extensions import (
    MISChatCompletionRequest,
    MISOpenAIServingChat
)
from mis.logger import init_logger, LogType
from mis.utils.utils import get_client_ip

logger = init_logger(__name__, log_type=LogType.OPERATION)
logger_service = init_logger(__name__+".service", log_type=LogType.SERVICE)

router = APIRouter()

# we only need vLLM /openai/v1/models return `id` `created` `object` `owned_by` `max_model_len`,
# so del `root` `parent` `permission`
MIS_MODEL_REMOVE_FIELDS = [
    "root", "parent", "permission"
]


@router.get("/openai/v1/models")
async def show_available_models(raw_request: Request):
    client_ip = get_client_ip(raw_request)
    logger_service.debug(f"Handling request to show available models.")
    handler = models(raw_request)

    try:
        if raw_request.app.state.request_timeout:
            available_models = await asyncio.wait_for(
                handler.show_available_models(),
                timeout=raw_request.app.state.request_timeout
            )
        else:
            available_models = await handler.show_available_models()
    except asyncio.TimeoutError:
        logger.error(f"[IP: {client_ip}] 'GET /openai/v1/models' {HTTPStatus.REQUEST_TIMEOUT.value} Request timeout")
        return JSONResponse(
            status_code=HTTPStatus.REQUEST_TIMEOUT.value,
            content={"detail": f"[IP: {client_ip}] Request timeout"}
        )

    for model_ in available_models.data:
        for field in MIS_MODEL_REMOVE_FIELDS:
            if hasattr(model_, field):
                delattr(model_, field)
    logger.info(f"[IP: {client_ip}] 'GET /openai/v1/models' {HTTPStatus.OK.value} OK")
    return JSONResponse(content=available_models.model_dump())


def _align_non_streaming_response(generator: ChatCompletionResponse) -> None:
    """
    remove stop_reason in vllm response to ensure consistent behavior
    """
    logger_service.debug(f"Aligning non-streaming response")
    for choice in generator.choices:
        del choice.stop_reason
    logger_service.debug(f"Non-streaming response aligned")


async def _align_streaming_response(generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
    """
    remove stop_reason in vllm stream response to ensure consistent behavior
    """
    logger_service.debug(f"Aligning streaming response")
    async for content in generator:
        if "stop_reason" in content:
            try:
                content_dict = json.loads(content[len("data: "):])
            except json.JSONDecodeError:
                logger_service.warning(f"Failed to parse JSON content")
                yield content
                continue

            if not isinstance(content_dict, dict):
                logger_service.warning(f"Content is not a dictionary")
                yield content
                continue

            try:
                content_obj = ChatCompletionStreamResponse(**content_dict)
            except ValidationError:
                logger_service.warning(f"Validation error in content object")
                yield content
                continue

            for choice in content_obj.choices:
                del choice.stop_reason

            yield f"data: {content_obj.model_dump_json(exclude_unset=True)}\n\n"
        else:
            yield content
    logger_service.debug(f"Streaming response aligned")


@router.post("/openai/v1/chat/completions")
async def create_chat_completions(request: MISChatCompletionRequest,
                                  raw_request: Request):
    client_ip = get_client_ip(raw_request)
    logger_service.debug(f"Handling request to create chat completions.")
    handler = chat(raw_request)
    if handler is None:
        logger.error(f"[IP: {client_ip}] 'POST /openai/v1/chat/completions' {HTTPStatus.BAD_REQUEST} "
                     f"The model does not support Chat Completions API")
        return base(raw_request).create_error_response(message="The model does not support Chat Completions API")
    try:
        if raw_request.app.state.request_timeout:
            generator = await asyncio.wait_for(
                handler.create_chat_completion(request, raw_request),
                timeout=raw_request.app.state.request_timeout
            )
        else:
            generator = await handler.create_chat_completion(request, raw_request)
    except asyncio.TimeoutError:
        logger.error(f"[IP: {client_ip}] 'POST /openai/v1/chat/completions' "
                     f"{HTTPStatus.REQUEST_TIMEOUT.value} Request timeout")
        return JSONResponse(
            status_code=HTTPStatus.REQUEST_TIMEOUT.value,
            content={"detail": f"Request timeout"}
        )

    if isinstance(generator, ErrorResponse):
        logger.error(f"[IP: {client_ip}] 'POST /openai/v1/chat/completions' {generator.code} Error in chat completion")
        return JSONResponse(content=generator.model_dump(),
                            status_code=generator.code)

    elif isinstance(generator, ChatCompletionResponse):
        _align_non_streaming_response(generator)
        logger.info(f"[IP: {client_ip}] 'POST /openai/v1/chat/completions' {HTTPStatus.OK.value} OK")
        return JSONResponse(content=generator.model_dump())

    generator = _align_streaming_response(generator)
    logger.info(f"[IP: {client_ip}] 'POST /openai/v1/chat/completions' {HTTPStatus.OK.value} OK")
    return StreamingResponse(content=generator, media_type="text/event-stream")


async def init_openai_app_state(
        engine_client: EngineClient,
        model_config: ModelConfig,
        state: State,
        args: GlobalArgs
) -> None:
    logger_service.info("Initializing OpenAI app state.")
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

    logger_service.info("Registering openai_serving_models.")
    # register openai_serving_models, will be use by function `models`
    state.openai_serving_models = OpenAIServingModels(
        engine_client=engine_client,
        model_config=model_config,
        base_model_paths=base_model_paths,
    )

    logger_service.info("Registering openai_serving_chat.")
    # register openai_serving_chat, will be use by function `chat`
    state.openai_serving_chat = MISOpenAIServingChat(
        engine_client,
        model_config,
        state.openai_serving_models,
        "assistant",
        request_logger=request_logger,
        chat_template=None,
        chat_template_content_format="auto",
    )

    logger_service.info("Registering openai_serving_tokenization.")
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
    state.request_timeout = REQUEST_TIMEOUT_IN_SEC
    logger_service.info("OpenAI app state initialized")
