# -*- coding: utf-8 -*-
# Copyright (c) Huawei Technologies Co., Ltd. 2025. All rights reserved.
import asyncio
import signal

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


def init_app_state(app, args: GlobalArgs):
    from mis.emb.entrypoints.clip.api_server import router
    app.include_router(router)


def run_clip_server(args: GlobalArgs):
    logger.info(f"MIS API server:{args.host}:{args.port}")

    def signal_handler(*_) -> None:
        raise KeyboardInterrupt("terminated")

    signal.signal(signal.SIGTERM, signal_handler)
    engine_client = None
    try:
        engine_client = build_engine_client_from_args(args)
    except Exception as e:
        logger.error(f"create engine error:{e}")

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
        run_clip_server(args)
    except Exception as e:
        logger.exception(f"clip launcher exit: {e}")


if __name__ == "__main__":
    main()
