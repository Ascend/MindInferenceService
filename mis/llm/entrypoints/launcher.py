#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Optional

import uvloop
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp
from vllm.config import ModelConfig
from vllm.engine.protocol import EngineClient
from vllm.entrypoints.launcher import serve_http
from vllm.entrypoints.openai.api_server import lifespan, create_server_socket
from vllm.utils import set_ulimit

from mis import constants
from mis.args import ARGS, GlobalArgs
from mis.hub.envpreparation import environment_preparation
from mis.llm.engine_factory import AutoEngine
from mis.llm.entrypoints.middleware import (RateLimitConfig, RequestSizeLimitMiddleware,
                                            RequestHeaderSizeLimitMiddleware,
                                            ConcurrencyLimitMiddleware, RateLimitMiddleware,
                                            RequestTimeoutMiddleware)
from mis.logger import init_logger, LogType
from mis.utils.utils import get_client_ip

logger = init_logger(__name__, log_type=LogType.SERVICE)
op_logger = init_logger(__name__ + ".operation", log_type=LogType.OPERATION)

TIMEOUT_KEEP_ALIVE = 5


@asynccontextmanager
async def lifespan(app: ASGIApp) -> None:
    """
    An async context manager that handles the application's startup and shutdown events.
    Args:
        app (ASGIApp): The ASGIApp application instance.
    Yields:
        None: Control is yielded back to the application to run.
    """
    logger.info("Application is starting up.")
    if app is None:
        logger.error("ASGIApp application instance is required and cannot be None.")
        raise ValueError("ASGIApp application instance is required and cannot be None.")
    yield
    logger.info("Application is shutting down.")
    if hasattr(app.state, "rate_limit_middleware"):
        logger.info("Shutting down rate limit middleware.")
        await app.state.rate_limit_middleware.shutdown()


@asynccontextmanager
async def _build_engine_client_from_args(args: GlobalArgs) -> EngineClient:
    """
    Context manager to build and manage the engine client from the given arguments.

    Args:
        args (GlobalArgs): The global arguments containing all configuration resolved by MIS.

    Yields:
        EngineClient: The initialized engine client.
    """
    engine_client: Optional[EngineClient] = None
    try:
        engine_client = AutoEngine.from_config(args)
        yield engine_client
    finally:
        if engine_client and hasattr(engine_client, "shutdown"):
            engine_client.shutdown()


def _add_exception_handlers(app: ASGIApp):
    @app.exception_handler(HTTPStatus.METHOD_NOT_ALLOWED)
    async def method_not_allowed_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Custom exception handler for HTTP 405 Method Not Allowed.
        Args:
            request (Request): The incoming HTTP request object.
            exc (Exception): The exception that was raised (e.g., MethodNotAllowed).
        Returns:
            JSONResponse: A JSON response with status code 405 and a message indicating
                          the unsupported method and the allowed methods.
        """
        client_ip = get_client_ip(request)
        op_logger.warning(f"[IP: {client_ip}] {HTTPStatus.METHOD_NOT_ALLOWED.value} "
                          "Request Method not allowed, allowed methods in ['GET', 'POST']")
        return JSONResponse(
            status_code=HTTPStatus.METHOD_NOT_ALLOWED,
            content={
                "message": f"Method {request.method} not allowed",
                "allowed_methods": ["GET", "POST"]
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        client_ip = get_client_ip(request)
        op_logger.error(f"[IP: {client_ip}] {HTTPStatus.BAD_REQUEST.value} Request validation error")
        return JSONResponse(
            status_code=HTTPStatus.BAD_REQUEST,
            content={
                "message": "Request validation error"
            },
        )

    @app.exception_handler(Exception)
    async def internal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        client_ip = get_client_ip(request)
        op_logger.error(f"[IP: {client_ip}] {HTTPStatus.INTERNAL_SERVER_ERROR.value} "
                        "Internal server error")
        return JSONResponse(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            content={
                "message": "Internal Server Error"
            },
        )


def _add_middlewares(args: GlobalArgs, app: ASGIApp):
    app.add_middleware(RequestHeaderSizeLimitMiddleware, max_header_size=constants.MAX_REQUEST_HEADER_SIZE)

    # Add request size limiting middleware using configured limit
    app.add_middleware(RequestSizeLimitMiddleware, max_body_size=constants.MAX_REQUEST_BODY_SIZE)

    # Add concurrent request limiting middleware using configured limit
    app.add_middleware(ConcurrencyLimitMiddleware, max_concurrent_requests=constants.MAX_CONCURRENT_REQUESTS)

    # Add rate limiting middleware
    rate_limit_config = RateLimitConfig(
        requests_per_minute=getattr(args, 'rate_limit_per_minute', constants.RATE_LIMIT_PER_MINUTE),
    )

    rate_limit_middleware = RateLimitMiddleware(app, config=rate_limit_config)
    app.add_middleware(rate_limit_middleware.__class__, config=rate_limit_config)
    app.add_middleware(RequestTimeoutMiddleware, request_timeout_in_sec=constants.REQUEST_TIMEOUT_IN_SEC)


def _add_restrict_host_middleware(app: ASGIApp):
    @app.middleware("http")
    async def restrict_host_middleware(request: Request, call_next: callable) -> JSONResponse:
        """
        Middleware to restrict access based on the Host header.
        Args:
            request (Request): The incoming HTTP request object.
            call_next (Callable): The next middleware or route handler in the chain.
        Returns:
            JSONResponse: The response from the next middleware or route handler if the host is allowed,
                          or a JSONResponse with status code 403 if the host is not allowed.
        """
        client_ip = get_client_ip(request)
        allowed_hosts = (constants.MIS_HOST,)
        if not callable(call_next):
            op_logger.warning(f"[IP: {client_ip}] {HTTPStatus.INTERNAL_SERVER_ERROR.value} "
                              f"call_next must be callable, got {type(call_next).__name__}")
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )
        try:
            host = request.headers.get("host", "").split(":")[0]
            if host not in allowed_hosts:
                op_logger.warning(f"[IP: {client_ip}] {HTTPStatus.FORBIDDEN.value} Invalid host")
                return JSONResponse(
                    status_code=HTTPStatus.FORBIDDEN,
                    content={"detail": "Forbidden: Invalid Host"}
                )
            return await call_next(request)
        except AttributeError as e:
            op_logger.error(
                f"[IP: {client_ip}] {HTTPStatus.INTERNAL_SERVER_ERROR.value} "
                "AttributeError in restrict_host_middleware")
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                content={"detail": "Internal Server Error"}
            )
        except Exception as e:
            op_logger.error(
                f"[IP: {client_ip}] {HTTPStatus.INTERNAL_SERVER_ERROR.value} "
                "Unexpected error in restrict_host_middleware")
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                content={"detail": "Internal Server Error"}
            )


def _build_app(args: GlobalArgs) -> ASGIApp:
    """
    Build the ASGIApp application based on the given arguments.
    Args:
        args (GlobalArgs): The global arguments containing all configuration resolved by MIS.
    Returns:
        ASGIApp: The configured ASGIApp application.
    """
    logger.debug("Disabling ASGIApp documentation")
    app = FastAPI(openapi_url=None,
                  docs_url=None,
                  redoc_url=None,
                  lifespan=lifespan,
                  redirect_slashes=False)

    if args.enable_dos_protection:
        _add_middlewares(args, app)
        logger.info(
            "Headers size limit, request size limit, concurrency limit, rate limit and timeout control middleware is enabled")
    else:
        logger.warning("The middleware is disabled. "
                       "For security, please correctly set MIS_ENABLE_DOS_PROTECTION.")
    _add_exception_handlers(app)
    _add_restrict_host_middleware(app)

    from mis.llm.entrypoints.openai.api_server import router as openai_router
    app.include_router(openai_router)

    return app


async def _init_app_state(engine_client: EngineClient, model_config: ModelConfig,
                          app: ASGIApp, args: GlobalArgs) -> None:
    """
    Initialize the application state with the given engine client, model configuration, and arguments.

    Args:
        engine_client (EngineClient): The engine client.
        model_config (ModelConfig): The model configuration.
        app (ASGIApp): The ASGIApp application.
        args (GlobalArgs): The global arguments containing all configuration resolved by MIS.
    """
    if args.engine_type in constants.MIS_ENGINE_TYPES:
        logger.info("Initializing OpenAI app state")
        from mis.llm.entrypoints.openai.api_server import router, init_openai_app_state
        logger.info(f"Check if the route has been registered.")
        if not any(router.prefix in r.path for r in router.routes):
            app.include_router(router)
        await init_openai_app_state(engine_client, model_config, app.state, args)
    else:
        logger.error(f"Available EngineType is in {constants.MIS_ENGINE_TYPES}")
        raise ValueError(f"Available EngineType is in {constants.MIS_ENGINE_TYPES}")


async def _run_server(args: GlobalArgs) -> None:
    """Starts the completions server using the vLLM engine.

    This function sets up a server socket, configures signal handling, builds the engine client, initializes the FastAPI
    application, and serves HTTP requests. It also handles graceful shutdown of the server.

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
        logger.info("Building ASGIApp application")
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
    """Main entry point for the application."""
    args = environment_preparation(ARGS)
    uvloop.run(_run(args))


if __name__ == "__main__":
    main()
