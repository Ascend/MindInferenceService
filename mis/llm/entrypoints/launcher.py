# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import os
import re
import signal
import sys
from contextlib import asynccontextmanager
from typing import Optional
from http import HTTPStatus

import uvloop
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.routing import Mount
from vllm.entrypoints.openai.api_server import lifespan, create_server_socket
from vllm.entrypoints.openai.protocol import ErrorResponse
from vllm.entrypoints.launcher import serve_http
from vllm.utils import set_ulimit

from mis.engine_factory import AutoEngine, EngineClient
from mis.logger import init_logger
from mis.args import GlobalArgs
from mis.hub.envpreparation import environment_preparation

logger = init_logger(__name__)

MIS_PROMETHEUS_URL = "/v1/metrics"
TIMEOUT_KEEP_ALIVE = 5


@asynccontextmanager
async def build_engine_client_from_args(args: GlobalArgs) -> EngineClient:
    engine_client: Optional[EngineClient] = None
    try:
        engine_client = AutoEngine.from_config(args)
        yield engine_client
    finally:
        if engine_client and hasattr(engine_client, "shutdown"):
            engine_client.shutdown()


def mount_metrics(app: FastAPI):
    from prometheus_client import CollectorRegistry, make_asgi_app, multiprocess

    prometheus_multiproc_dir_path = os.getenv("PROMETHEUS_MULTIPROC_DIR", None)
    if prometheus_multiproc_dir_path is not None:
        logger.debug("MIS use %s as PROMETHEUS_MULTIPROC_DIR",
                     prometheus_multiproc_dir_path)
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)

        metrics_route = Mount(MIS_PROMETHEUS_URL, make_asgi_app(registry=registry))
    else:
        metrics_route = Mount(MIS_PROMETHEUS_URL, make_asgi_app())

    metrics_route.path_regex = re.compile(f"^{MIS_PROMETHEUS_URL}(?P<path>.*)$")
    app.routes.append(metrics_route)


def build_app(args: GlobalArgs) -> FastAPI:
    if args.disable_fastapi_docs:
        app = FastAPI(openapi_url=None,
                      docs_url=None,
                      redoc_url=None,
                      lifespan=lifespan)
    else:
        app = FastAPI(lifespan=lifespan)

    mount_metrics(app)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_, exc):
        error = ErrorResponse(message=str(exc),
                              type="BadRequestError",
                              code=HTTPStatus.BAD_REQUEST)
        return JSONResponse(content=error.model_dump(),
                            status_code=HTTPStatus.BAD_REQUEST)

    return app


async def run_server(args: GlobalArgs):
    logger.info("MIS API server")
    logger.info("args: %s", args)

    sock_addr = (args.host or "", args.port)
    sock = create_server_socket(sock_addr)

    set_ulimit()

    def signal_handler(*_) -> None:
        raise KeyboardInterrupt("terminated")

    signal.signal(signal.SIGTERM, signal_handler)

    async with build_engine_client_from_args(args) as engine_client:
        app = build_app(args)

        app.state.engine_client = engine_client
        app.state.log_stats = not args.disable_log_stats

        model_config = await engine_client.get_model_config()

        from mis.llm.entrypoints.openai.api_server import register_openai_app, init_openai_app_state
        register_openai_app(app, args)
        await init_openai_app_state(engine_client, model_config, app.state, args)

        shutdown_task = await serve_http(
            app,
            host=args.host,
            port=args.port,
            log_level=args.uvicorn_log_level,
            timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            ssl_ca_certs=args.ssl_ca_certs,
            ssl_cert_reqs=args.ssl_cert_reqs,
            fd=sock.fileno() if sys.platform.startswith("darwin") else None
        )

    await shutdown_task

    sock.close()


if __name__ == "__main__":
    args = GlobalArgs()
    args = environment_preparation(args)

    uvloop.run(run_server(args))
