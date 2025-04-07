# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
import json
import time
import uuid
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

    @staticmethod
    def _field_exist(o, key):
        if not isinstance(o, dict):
            return False
        return key in o

    @staticmethod
    def _field_exist_and_is_str(o, key):
        if not MindIEServiceChat._field_exist(o, key):
            return False
        return isinstance(o[key], str)

    @staticmethod
    def _field_exist_and_is_dict(o, key):
        if not MindIEServiceChat._field_exist(o, key):
            return False
        return isinstance(o[key], dict)

    @staticmethod
    def _field_exist_and_is_list(o, key):
        if not MindIEServiceChat._field_exist(o, key):
            return False
        return isinstance(o[key], list)

    @staticmethod
    def _process_stream_line(line, id: str, created: str, first_line: bool) -> (str, str):
        created = str(int(time.time())) if not created else created
        if not line or line == "data: [DONE]":
            return line, created

        try:
            line_obj = json.loads(line[len("data: "):])
        except json.JSONDecodeError:
            return "", created

        if not isinstance(line_obj, dict):
            return "", created

        line_obj["id"] = id
        if MindIEServiceChat._field_exist(line_obj, "usage"):
            del line_obj["usage"]
        if not MindIEServiceChat._field_exist_and_is_list(line_obj, "choices") or \
                len(line_obj["choices"]) != 1 or \
                not isinstance(line_obj["choices"][0], dict):
            return "", created

        choice = line_obj["choices"][0]
        choice["logprobs"] = None
        if first_line:
            if MindIEServiceChat._field_exist_and_is_str(line_obj, "created"):
                created = line_obj["created"]

            if not MindIEServiceChat._field_exist_and_is_dict(choice, "delta") or \
                    not MindIEServiceChat._field_exist(choice["delta"], "content") or \
                    not MindIEServiceChat._field_exist(choice["delta"], "role"):
                return "", created

            content = choice["delta"]["content"]
            choice["delta"]["content"] = ""
            line0 = f"data: {json.dumps(line_obj, ensure_ascii=False, separators=(',', ':'))}"

            del choice["delta"]["role"]
            choice["delta"]["content"] = content
            line1 = f"data: {json.dumps(line_obj, ensure_ascii=False, separators=(',', ':'))}"
            return f"{line0}\n\n{line1}", created
        else:
            line_obj["created"] = created
            if MindIEServiceChat._field_exist_and_is_dict(choice, "delta") and \
                    MindIEServiceChat._field_exist(choice["delta"], "role"):
                del choice["delta"]["role"]
            return f"data: {json.dumps(line_obj, ensure_ascii=False, separators=(',', ':'))}", created

    async def chat_completions_stream_generator(self, request: MISChatCompletionRequest):
        try:
            with httpx.stream("POST",
                              url=f"http://{self.config.address}:{self.config.server_port}/v1/chat/completions",
                              json=request.dict(),
                              timeout=60) as r:
                if r.status_code != HTTPStatus.OK:
                    raise Exception("MindIE Service response error")
                id = "chatcmpl-" + str(uuid.uuid4().hex)
                first_line = True
                created = None
                for line in r.iter_lines():
                    await asyncio.sleep(0)
                    new_line, created = self._process_stream_line(line, id, created=created, first_line=first_line)
                    first_line = False
                    yield f"{new_line}\n"
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
            res = response.json()

            res["id"] = "chatcmpl-" + str(uuid.uuid4().hex)
            res["prompt_logprobs"] = None

            if not MindIEServiceChat._field_exist_and_is_list(res, "choices") or \
                    len(res["choices"]) != 1 or \
                    not isinstance(res["choices"][0], dict):
                raise ValueError("MindIE-Service response with invalid choices")
            choice = res["choices"][0]
            if MindIEServiceChat._field_exist_and_is_dict(choice, "message"):
                choice["message"]["reasoning_content"] = None
            choice["logprobs"] = None

            if MindIEServiceChat._field_exist_and_is_dict(res, "usage"):
                res["usage"]["prompt_tokens_details"] = None
            if MindIEServiceChat._field_exist(res, "decode_time_arr"):
                del res["decode_time_arr"]
            if MindIEServiceChat._field_exist(res, "prefill_time"):
                del res["prefill_time"]

            return res
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
