# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
from http import HTTPStatus
from typing import Union, AsyncGenerator

import httpx
from fastapi import APIRouter, Request
from starlette.datastructures import State
from starlette.responses import JSONResponse, StreamingResponse
from vllm.config import ModelConfig
from vllm.engine.protocol import EngineClient
from vllm.entrypoints.utils import with_cancellation
from vllm.entrypoints.openai.protocol import ErrorResponse
from vllm.entrypoints.openai.serving_models import OpenAIServingModels, BaseModelPath

from mis.args import GlobalArgs
from mis.llm.engines.mindie.engine import MindIEServiceArgs
from mis.llm.entrypoints.openai.api_extensions import MISChatCompletionRequest
from mis.logger import init_logger

logger = init_logger(__name__)

router = APIRouter()


@router.get("/openai/v1/models")
async def show_available_models(raw_request: Request):
    handler = raw_request.app.state.mindie_models

    models_ = await handler.show_available_models()
    return JSONResponse(content=models_.model_dump())


@router.post("/openai/v1/chat/completions")
@with_cancellation
async def create_chat_completion(request: MISChatCompletionRequest,
                                 raw_request: Request):
    handler = raw_request.app.state.mindie_chat
    generator = await handler.create_chat_completion(request)

    if isinstance(generator, ErrorResponse):
        return JSONResponse(content=generator.model_dump(),
                            status_code=generator.code)

    if isinstance(generator, dict):
        return JSONResponse(content=generator)

    return StreamingResponse(content=generator, media_type="text/event-stream")


class MindIEServiceChat:

    def __init__(self, engine: EngineClient):
        self.engine = engine
        if not hasattr(self.engine, "mindie_args"):
            raise ValueError("MindIEServiceChat can not find mindie_args in engine")
        self.config: MindIEServiceArgs = engine.mindie_args

    @staticmethod
    def create_error_response(message: str,
                              err_type: str = "BadRequestError",
                              status_code: HTTPStatus = HTTPStatus.BAD_REQUEST) -> ErrorResponse:
        return ErrorResponse(message=message,
                             type=err_type,
                             code=status_code.value)

    async def create_chat_completion(
            self, request: MISChatCompletionRequest
    ) -> Union[AsyncGenerator[str, None], ErrorResponse, dict]:
        try:
            if request.stream:
                return self.chat_completions_stream_generator(request)
            else:
                return await self.chat_completions_full_generator(request)
        except Exception as e:
            return self.create_error_response(str(e))

    async def chat_completions_stream_generator(self, request: MISChatCompletionRequest):
        try:
            with httpx.stream("POST",
                              url=f"http://{self.config.address}:{self.config.server_port}/v1/chat/completions",
                              json=request.dict(),
                              timeout=60) as r:
                if r.status_code != HTTPStatus.OK:
                    raise Exception("MindIE Service response error")
                for line in r.iter_lines():
                    await asyncio.sleep(0)
                    yield f"{line}\n"
        except asyncio.CancelledError:
            logger.warning(f"request:{request.request_id} is cancelled")
            raise

    async def chat_completions_full_generator(self, request: MISChatCompletionRequest) -> dict:
        try:
            response = httpx.post(f"http://{self.config.address}:{self.config.server_port}/v1/chat/completions",
                                  json=request.dict(),
                                  timeout=600)
            if response.status_code != HTTPStatus.OK:
                raise Exception("MindIE Service response error")
            return response.json()
        except asyncio.CancelledError:
            logger.warning(f"request:{request.request_id} is cancelled")
            raise


async def init_mindie_app_state(engine_client: EngineClient,
                                model_config: ModelConfig,
                                state: State,
                                args: GlobalArgs):
    base_model_paths = [
        BaseModelPath(name=model_config.served_model_name, model_path=args.model)
    ]

    state.mindie_models = OpenAIServingModels(
        engine_client=engine_client,
        model_config=model_config,
        base_model_paths=base_model_paths
    )

    state.mindie_chat = MindIEServiceChat(engine_client)
