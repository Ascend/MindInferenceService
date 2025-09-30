# -*- coding:utf-8 -*-
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Optional

import uvloop
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from vllm.config import ModelConfig
from vllm.engine.protocol import EngineClient
from vllm.entrypoints.launcher import serve_http
from vllm.entrypoints.openai.api_server import lifespan, create_server_socket
from vllm.entrypoints.openai.protocol import ErrorResponse
from vllm.utils import set_ulimit

from mis import constants
from mis.args import ARGS, GlobalArgs
from mis.hub.envpreparation import environment_preparation
from mis.llm.engine_factory import AutoEngine
from mis.logger import init_logger

logger = init_logger(__name__)

TIMEOUT_KEEP_ALIVE = 5


@asynccontextmanager
async def _build_engine_client_from_args(args: GlobalArgs) -> EngineClient:
    engine_client: Optional[EngineClient] = None
    try:
        engine_client = AutoEngine.from_config(args)
        yield engine_client
    finally:
        if engine_client and hasattr(engine_client, "shutdown"):
            engine_client.shutdown()


def _build_app(args: GlobalArgs) -> FastAPI:
    if args.disable_fastapi_docs:
        logger.info("Disabling FastAPI documentation")
        app = FastAPI(openapi_url=None,
                      docs_url=None,
                      redoc_url=None,
                      lifespan=lifespan)
    else:
        logger.info("Enabling FastAPI documentation")
        app = FastAPI(lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: FastAPI, exc: RequestValidationError) -> JSONResponse:
        error = ErrorResponse(message=str(exc),
                              type="BadRequestError",
                              code=HTTPStatus.BAD_REQUEST)
        return JSONResponse(content=error.model_dump(),
                            status_code=HTTPStatus.BAD_REQUEST)

    return app


async def _init_app_state(engine_client: EngineClient, model_config: ModelConfig,
                          app: FastAPI, args: GlobalArgs) -> None:
    if args.engine_type in constants.MIS_ENGINE_TYPES:
        logger.info("Initializing OpenAI app state")
        from mis.llm.entrypoints.openai.api_server import router, init_openai_app_state
        app.include_router(router)
        await init_openai_app_state(engine_client, model_config, app.state, args)
    else:
        logger.error(f"Available EngineType is in {constants.MIS_ENGINE_TYPES}")
        raise ValueError(f"Available EngineType is in {constants.MIS_ENGINE_TYPES}")


async def _run_server(args: GlobalArgs) -> None:
    """Starts the completions server using the vLLM engine.

    This function sets up a server socket, configures signal handling, builds the engine client, initializes the FastAPI
    application, and serves HTTP/HTTPS requests. It also handles graceful shutdown of the server.

    Args:
        args: global args containing all configuration resolved by MIS.
    """

    logger.info("MIS API server starting")
    sock_addr = (args.host or "", args.port)
    sock = create_server_socket(sock_addr)
    logger.debug("Setting ulimit")
    set_ulimit()

    def signal_handler(*_: object) -> None:
        logger.error("Received SIGTERM, terminating")
        raise KeyboardInterrupt("terminated")

    signal.signal(signal.SIGTERM, signal_handler)

    async with _build_engine_client_from_args(args) as engine_client:
        logger.info("Building FastAPI application")
        app = _build_app(args)

        app.state.engine_client = engine_client
        app.state.log_stats = not args.disable_log_stats

        logger.info("Getting model configuration")
        model_config = await engine_client.get_model_config()

        logger.info("Initializing app state")
        await _init_app_state(engine_client, model_config, app, args)

        logger.info("Starting HTTP server")
        shutdown_task = await serve_http(
            app,
            host=args.host,
            port=args.port,
            sock=sock,
            log_level=args.uvicorn_log_level,
            timeout_keep_alive=TIMEOUT_KEEP_ALIVE,
            ssl_keyfile=args.ssl_keyfile,
            ssl_certfile=args.ssl_certfile,
            ssl_ca_certs=args.ssl_ca_certs,
            ssl_cert_reqs=args.ssl_cert_reqs,
            ssl_ciphers=constants.MIS_SSL_CIPHERS,
            fd=sock.fileno() if sys.platform.startswith("darwin") else None
        )

    logger.info("Shutting down server")
    await shutdown_task

    logger.info("Closing server socket")
    sock.close()


async def _run(args: GlobalArgs) -> None:
    """Starts both the main server.

    This function creates and runs two asynchronous tasks: one for the main server.
    It waits for either of the tasks to complete. If one task completes (or is cancelled), the other task is cancelled.

    Args:
        args: global args containing all configuration resolved by MIS.
    """

    loop = asyncio.get_running_loop()
    server_task = loop.create_task(_run_server(args))

    logger.info("Starting server tasks")
    done, pending = await asyncio.wait([server_task], return_when=asyncio.FIRST_COMPLETED)

    for p in pending:
        logger.info("Cancelling pending tasks")
        p.cancel()

    # raise exceptions that occurred in the done tasks to prevents swallowing exceptions.
    for d in done:
        try:
            d.result()
        except Exception as e:
            logger.error(f"Server running failed: {e}")
            raise Exception("Server running failed") from e


def main() -> None:
    args = environment_preparation(ARGS)
    uvloop.run(_run(args))


if __name__ == "__main__":
    main()
