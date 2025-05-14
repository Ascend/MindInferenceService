# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import json
import os
from http import HTTPStatus
from typing import Union, List, Dict, Optional

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
            logger.error("TEI Service response error")
            return JSONResponse(status_code=response.status_code, content={"error_info": response.text})

        try:
            res_dict = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"TEI Service response json non-deserializable object: {e}")
            return JSONResponse(status_code=HTTPStatus.MISDIRECTED_REQUEST,
                                content={"error_info": response.text})

        return JSONResponse(content=res_dict)


async def deal_get_request(url: str):
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10)
        if response.status_code != HTTPStatus.OK:
            logger.error("TEI Service response error")
            return JSONResponse(status_code=response.status_code, content=response.content)

        try:
            res_text = response.text
        except Exception as e:
            logger.error(f"get response content failed: {e}")
            return JSONResponse(status_code=HTTPStatus.MISDIRECTED_REQUEST,
                                content={"error": "TEI service response data error"})
        if res_text:
            return JSONResponse(content=json.loads(res_text))
        else:
            return JSONResponse(content={})


class DecodeRequest(BaseModel):
    ids: List[int]
    skip_special_tokens: bool = True


@router.post("/decode")
async def embed(decode_request: DecodeRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/decode", decode_request.dict())
    return res


class EmbedRequest(BaseModel):
    inputs: Union[str, List[str]]
    normalize: bool = True
    prompt_name: Optional[str] = Field(None)
    truncate: bool = False
    truncation_direction: str = "Right"


@router.post("/embed")
async def embed(embed_request: EmbedRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/embed", embed_request.dict())
    return res


class EmbeddingsRequest(BaseModel):
    input: Union[str, List[str]]
    encoding_format: str = "float"
    model: str = ""
    user: str = ""


@router.post("/v1/embeddings")
async def openai_embed(embeddings_request: EmbeddingsRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/v1/embeddings", embeddings_request.dict())
    return res


class EmbedAllRequest(BaseModel):
    inputs: Union[str, List[str]]
    prompt_name: Optional[str] = Field(None)
    truncate: bool = False
    truncation_direction: str = "Right"


@router.post("/embed_all")
async def embed_all(embed_all_request: EmbedAllRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/embed_all", embed_all_request.dict())
    return res


class EmbedSparseRequest(BaseModel):
    inputs: Union[str, List[str]]
    prompt_name: Optional[str] = Field(None)
    truncate: bool = False
    truncation_direction: str = "Right"


@router.post("/embed_sparse")
async def embed_sparse(embed_sparse_request: EmbedSparseRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/embed_sparse", embed_sparse_request.dict())
    return res


class PredictRequest(BaseModel):
    inputs: Union[str, List[str]]
    raw_scores: bool = False
    truncate: bool = False
    truncation_direction: str = "Right"


@router.post("/predict")
async def predict(predict_request: PredictRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/predict", predict_request.dict())
    return res


class RerankRequest(BaseModel):
    query: str
    texts: List[str]
    raw_scores: bool = False
    return_text: bool = False
    truncate: bool = False
    truncation_direction: str = "Right"


@router.post("/rerank")
async def rerank(rerank_request: RerankRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/rerank", rerank_request.dict())
    return res


class TokenizeRequest(BaseModel):
    inputs: Union[str, List[str]]
    add_special_tokens: bool = True
    prompt_name: Optional[str] = Field(None)


@router.post("/tokenize")
async def tokenize(tokenize_request: TokenizeRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/tokenize", tokenize_request.dict())
    return res


class SimilarityRequest(BaseModel):
    inputs: dict


@router.post("/similarity")
async def similarity(similarity_request: SimilarityRequest, raw_request: Request):
    res = await deal_post_request(f"http://127.0.0.1:{ARGS.inner_port}/similarity", similarity_request.dict())
    return res


@router.get("/health")
async def health(raw_request: Request):
    res = await deal_get_request(f"http://127.0.0.1:{ARGS.inner_port}/health")
    return res


@router.get("/info")
async def info(raw_request: Request):
    res = await deal_get_request(f"http://127.0.0.1:{ARGS.inner_port}/info")
    return res


@router.get("/metrics")
async def metrics(raw_request: Request):
    res = await deal_get_request(f"http://127.0.0.1:{ARGS.inner_port}/metrics")
    return res
