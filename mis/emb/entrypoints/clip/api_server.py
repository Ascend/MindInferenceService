# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025. All rights reserved.
import json
from http import HTTPStatus
from typing import Dict

import httpx
from fastapi import APIRouter, Request
from loguru import logger
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from mis.args import ARGS

router = APIRouter()


async def deal_post_request(url: str, body: Dict):
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body, timeout=5 * 60)
        if response.status_code != HTTPStatus.OK:
            logger.error("Clip Service response error")
            return JSONResponse(status_code=response.status_code, content={"error_info": response.text})

        try:
            res_dict = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Clip Service response json non-deserializable object: {e}")
            return JSONResponse(status_code=HTTPStatus.MISDIRECTED_REQUEST,
                                content={"error_info": response.text})

        return JSONResponse(content=res_dict)


async def deal_get_request(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        if response.status_code != HTTPStatus.OK:
            logger.error("Clip Service response error")
            return JSONResponse(status_code=response.status_code, content=response.content)

        try:
            res_text = response.text
        except Exception as e:
            logger.error(f"get response content failed: {e}")
            return JSONResponse(status_code=HTTPStatus.MISDIRECTED_REQUEST,
                                content={"error": "Clip service response data error"})
        if res_text:
            return JSONResponse(content=json.loads(res_text))
        else:
            return JSONResponse(content={})


class EncodeRequest(BaseModel):
    data: list[dict]
    parameters: dict = {"drop_image_content": True}


@router.post("/encode")
async def embed(embed_request: EncodeRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/encode", embed_request.dict())
    return res
