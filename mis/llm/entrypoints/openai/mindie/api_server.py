# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
import json
import time
import uuid
from http import HTTPStatus
from typing import Union, AsyncGenerator

import httpx
import pydantic
from fastapi import APIRouter, Request
from starlette.datastructures import State
from starlette.responses import JSONResponse, StreamingResponse
from vllm.config import ModelConfig
from vllm.engine.protocol import EngineClient
from vllm.entrypoints.openai.protocol import ErrorResponse, ChatCompletionResponse, ChatCompletionStreamResponse
from vllm.entrypoints.openai.serving_models import OpenAIServingModels, BaseModelPath

from mis.args import GlobalArgs
from mis.llm.engines.mindie.engine import MindIEServiceArgs
from mis.llm.entrypoints.openai.api_extensions import MISChatCompletionRequest
from mis.logger import init_logger

logger = init_logger(__name__)

router = APIRouter()

# we only need vLLM /openai/v1/models return `id` `created` `object` `owned_by` `max_model_len`,
# so del `root` `parent` `permission`
MIS_MODEL_REMOVE_FIELDS = [
    "root", "parent", "permission"
]


@router.get("/openai/v1/models")
async def show_available_models(raw_request: Request):
    handler = raw_request.app.state.mindie_models

    models_ = await handler.show_available_models()
    for model_ in models_.data:
        for field in MIS_MODEL_REMOVE_FIELDS:
            if hasattr(model_, field):
                delattr(model_, field)

    return JSONResponse(content=models_.model_dump())


@router.post("/openai/v1/chat/completions")
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

    @staticmethod
    def _gen_random_id():
        return "chatcmpl-" + str(uuid.uuid4().hex)

    @staticmethod
    def _process_stream_line(line, res_id: str, created: str, first_line: bool, include_usage: bool) -> (str, str):
        created = str(int(time.time())) if not created else created

        if not line or line == "data: [DONE]":
            return line, created

        try:
            line_dict = json.loads(line[len("data: "):])
        except json.JSONDecodeError:
            return "", created

        if not isinstance(line_dict, dict):
            return "", created

        try:
            line_obj = ChatCompletionStreamResponse(**line_dict)
        except pydantic.ValidationError:
            return "", created

        response_list = []

        line_obj.id = res_id

        # extract non-public fields for assemble later
        success, data = MindIEServiceChat._extract_field(line_obj)
        if not success:
            return "", created

        if first_line:
            line_str, created = MindIEServiceChat._process_first_line(line_obj, role=data.get("role", ""))
            response_list.append(line_str)
        else:
            line_obj.created = int(created)

        # when mindie-service api response changed, modify here to assemble response for consistent with vllm
        line_obj.choices[0].delta.content = data.get("content", "")
        line_obj.choices[0].finish_reason = data.get("finish_reason", "")
        response_list.append(f"data: {line_obj.model_dump_json(exclude_unset=True)}")
        del line_obj.choices[0].delta.content

        if data.get("usage") is not None and include_usage:
            line_obj.usage = data.get("usage")
            line_obj.choices = []
            response_list.append(f"data: {line_obj.model_dump_json(exclude_unset=True)}")

        return "\n\n".join(response_list), created

    @staticmethod
    def _extract_field(line_obj: ChatCompletionStreamResponse) -> (bool, dict):
        usage = None
        if line_obj.usage:
            usage = line_obj.usage
            del line_obj.usage

        if len(line_obj.choices) != 1:
            return False, {}
        choice = line_obj.choices[0]

        role = choice.delta.role
        del choice.delta.role

        content = choice.delta.content
        del choice.delta.content

        finish_reason = choice.finish_reason
        choice.finish_reason = None

        choice.logprobs = None

        return True, {"usage": usage, "role": role, "content": content, "finish_reason": finish_reason}

    @staticmethod
    def _process_first_line(line_obj: ChatCompletionStreamResponse, role) -> (str, str):
        created = str(line_obj.created)

        choice = line_obj.choices[0]

        choice.delta.role = role
        choice.delta.content = ""
        line_str = f"data: {line_obj.model_dump_json(exclude_unset=True)}"
        del choice.delta.role
        del choice.delta.content

        return line_str, created

    @staticmethod
    def _multimodal_file_contents_preprocess(contents):
        for content in contents:
            content_type = content.get("type", "")
            if "url" in content_type:
                url = content.get(content_type, {}).get("url", "")
                # Unified MindIE and vLLM multimodal (file) chat request url
                if url.startswith("file:"):
                    content[content_type]["url"] = url.replace("file:", "file://", 1)

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
        include_usage = False
        try:
            request = self._multimodal_file_request_preprocess(request)
        except Exception as e:
            logger.warning(f"MindIE multimodal file chat request conversion failed, "
                           f"will send original request to inference backend")
        if request.stream_options and request.stream_options.include_usage:
            include_usage = True
        try:
            with httpx.stream("POST",
                              url=f"http://{self.config.address}:{self.config.server_port}/v1/chat/completions",
                              json=request.dict(),
                              timeout=60) as r:
                if r.status_code != HTTPStatus.OK:
                    raise Exception("MindIE Service response error")
                res_id = self._gen_random_id()
                first_line = True
                created = ""
                for line in r.iter_lines():
                    await asyncio.sleep(0)
                    new_line, created = self._process_stream_line(
                        line, res_id, created=created, first_line=first_line, include_usage=include_usage)
                    first_line = False
                    yield f"{new_line}\n"
        except asyncio.CancelledError:
            logger.warning(f"request:{request.request_id} is cancelled")
            raise

    async def chat_completions_full_generator(self, request: MISChatCompletionRequest) -> dict:
        try:
            request = self._multimodal_file_request_preprocess(request)
        except Exception as e:
            logger.warning(f"MindIE multimodal file chat request conversion failed, "
                           f"will send original request to inference backend")
        try:
            response = httpx.post(f"http://{self.config.address}:{self.config.server_port}/v1/chat/completions",
                                  json=request.dict(),
                                  timeout=600)
            if response.status_code != HTTPStatus.OK:
                raise Exception("MindIE Service response error")

            try:
                res_dict = response.json()
            except json.JSONDecodeError as e:
                raise Exception("MindIE Service response json non-deserializable object") from e

            if not isinstance(res_dict, dict):
                raise ValueError("MindIE Service response with invalid format")

            res_dict["id"] = self._gen_random_id()

            choices = None
            if "choices" in res_dict:
                choices = res_dict["choices"]
            choice = None
            if isinstance(choices, list) and len(choices) == 1:
                choice = choices[0]
            message = None
            if isinstance(choice, dict) and "message" in choice:
                message = choice["message"]
            if isinstance(message, dict) and "tool_calls" in message and message["tool_calls"] is None:
                del message["tool_calls"]

            try:
                res_obj = ChatCompletionResponse(**res_dict)
            except pydantic.ValidationError as e:
                raise Exception("MindIE Service response failed") from e

            if hasattr(res_obj, "prefill_time"):
                delattr(res_obj, "prefill_time")
            if hasattr(res_obj, "decode_time_arr"):
                delattr(res_obj, "decode_time_arr")
            for choice in res_obj.choices:
                del choice.stop_reason

            return res_obj.model_dump()
        except asyncio.CancelledError:
            logger.warning(f"request:{request.request_id} is cancelled")
            raise

    def _multimodal_file_request_preprocess(self, request: MISChatCompletionRequest):
        for message in request.messages:
            contents = message.get("content", [])
            if isinstance(contents, list):
                self._multimodal_file_contents_preprocess(contents)
        return request


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
