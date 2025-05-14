# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
import os
import signal
import sys

import uvicorn
from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.requests import Request

from mis.args import ARGS, GlobalArgs
from mis.engine_factory import AutoEngine
from mis.hub.envpreparation import environment_preparation

TIMEOUT_KEEP_ALIVE = 5


def build_engine_client_from_args(args: GlobalArgs):
    return AutoEngine.from_config(args)


def register_tei_app(app: FastAPI,
                     args: GlobalArgs,
                     router: APIRouter):
    app.include_router(router)

    if args.api_key is not None:
        token = args.api_key

        @app.middleware("http")
        async def authentication(request: Request, call_next):
            if request.method == "OPTIONS":
                return await call_next(request)

            if request.headers.get("Authorization") != "Bearer " + token:
                return JSONResponse(content={"error": "Unauthorized"},
                                    status_code=401)


def init_app_state(app, args: GlobalArgs):
    from mis.emb.entrypoints.tei.api_server import router
    register_tei_app(app, args, router)


def run_tei_server(args: GlobalArgs):
    logger.info(f"MIS API server:{args.host}:{args.port}")

    def signal_handler(*_) -> None:
        raise KeyboardInterrupt("terminated")

    signal.signal(signal.SIGTERM, signal_handler)
    engine_client = None
    try:
        engine_client = build_engine_client_from_args(args)
    except Exception as e:
        logger.error(f"create engine meet error:{e}")

    if engine_client is None:
        logger.error(f"create engine failed")
        return

    if args.disable_fastapi_docs:
        app = FastAPI(openapi_url=None,
                      docs_url=None,
                      redoc_url=None)
    else:
        app = FastAPI()

    init_app_state(app, args)

    uvicorn.run(app, host=args.host,
                port=args.port,
                log_level=args.uvicorn_log_level,
                timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
                ssl_keyfile=args.ssl_keyfile,
                ssl_certfile=args.ssl_certfile,
                ssl_ca_certs=args.ssl_ca_certs,
                ssl_cert_reqs=args.ssl_cert_reqs)


def main():
    args = environment_preparation(ARGS)
    try:
        run_tei_server(args)
    except Exception as e:
        logger.exception(f"tei launcher exit: {e}")


if __name__ == "__main__":
    main()
