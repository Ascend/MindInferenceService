#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass
from http import HTTPStatus
from typing import Dict, Optional, Tuple, Union

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.types import ASGIApp
from starlette.requests import Request


from mis import constants
from mis.logger import init_logger, LogType
from mis.utils.utils import get_client_ip

logger = init_logger(__name__, log_type=LogType.OPERATION)
logger_service = init_logger(__name__+".service", log_type=LogType.SERVICE)

MINUTE_SECONDS = 60
CLEANUP_INTERVAL_SECONDS = 300
MAX_HEADER_COUNT = 200


@dataclass
class RateLimitConfig:
    """Rate limiting configuration"""
    requests_per_minute: int = constants.RATE_LIMIT_PER_MINUTE
    cleanup_interval: int = 600  # Cleanup interval in seconds


class RequestHeaderSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for limiting request header size"""
    def __init__(self, app: Union[FastAPI, ExceptionMiddleware],
                 max_header_size: int = constants.MAX_REQUEST_HEADER_SIZE) -> None:
        """ Initialize middleware with maximum header size limit
        Args:
            app (FastAPI, ExceptionMiddleware): The FastAPI application instance.
            max_header_size (int): Maximum allowed size for request headers in bytes
        """
        if not isinstance(app, (FastAPI, ExceptionMiddleware)):
            logger_service.error("FastAPI app instance is required for RequestHeaderSizeLimitMiddleware")
            raise TypeError("FastAPI app instance is required for RequestHeaderSizeLimitMiddleware")
        if not isinstance(max_header_size, int):
            logger_service.error("Integer value is required for max_header_size in RequestHeaderSizeLimitMiddleware")
            raise TypeError("Integer value is required for max_header_size in RequestHeaderSizeLimitMiddleware")
        super().__init__(app)
        self.max_header_size = max_header_size

    async def dispatch(self, request: Request, call_next: callable) -> JSONResponse:
        """ Check request header size and reject if it exceeds the limit
        Args:
            request (Request): The incoming request
            call_next (Callable): The next middleware or application callable
        """
        client_ip = get_client_ip(request)
        url = request.url.path
        if not callable(call_next):
            logger.warning(f"[IP: {client_ip}] '{url}' {HTTPStatus.INTERNAL_SERVER_ERROR.value} "
                           f"call_next must be callable, got {type(call_next).__name__}")
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error: invalid RequestSizeLimitMiddleware configuration"}
            )

        header_size = 0
        try:
            if len(request.headers) > MAX_HEADER_COUNT:
                logger.error(f"[IP: {client_ip}] '{url}' {HTTPStatus.BAD_REQUEST.value} Too many headers")
                return JSONResponse(status_code=HTTPStatus.BAD_REQUEST, content={"detail": "Too many headers"})
            for name, value in request.headers.items():
                header_size += len(name.encode('utf-8')) + len(b": ") + len(value.encode('utf-8'))
        except Exception as e:
            logger.error(f"[IP: {client_ip}] '{url}' {HTTPStatus.BAD_REQUEST.value} Error parsing request headers: {e}")
            return JSONResponse(
                status_code=HTTPStatus.BAD_REQUEST,
                content={"detail": "Error parsing request headers"}
            )
        if header_size > self.max_header_size:
            logger.warning(
                f"[IP: {client_ip}] '{url}' {HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE.value} "
                f"Request headers too large: {header_size} bytes, limit: {self.max_header_size} bytes")
            return JSONResponse(
                status_code=HTTPStatus.REQUEST_HEADER_FIELDS_TOO_LARGE,
                content={"detail": f"Request headers too large. Maximum size: {self.max_header_size} bytes"}
            )

        response = await call_next(request)
        return response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for limiting the size of the request body."""
    def __init__(self, app: FastAPI, max_body_size: int = constants.MAX_REQUEST_BODY_SIZE) -> None:  # Default 50MB
        """
        Initialize the middleware with the given FastAPI app and maximum body size.
        Args:
            app (FastAPI): The FastAPI application instance.
            max_body_size (int): The maximum allowed request body size in bytes. Default is 50MB.
        """
        super().__init__(app)
        self.max_body_size = max_body_size

    async def dispatch(self, request: Request, call_next: callable) -> JSONResponse:
        """
        Dispatch the request and check the size of the request body.
        Args:
            request (Request): The incoming HTTP request.
            call_next (Callable): The next middleware or route handler in the chain.
        Returns:
            Response: The response from the next middleware or route handler.
        """
        content_length_check = self._check_content_length(request)
        if content_length_check is not None:
            return content_length_check

        # Check if it is a chunked transfer encoding
        self._handle_chunked_transfer(request)

        response = await call_next(request)
        return response

    def _check_content_length(self, request: Request) -> Optional[JSONResponse]:
        """
        Check the Content-Length header to determine if the request body size is within the limit.
        Args:
            request (Request): The incoming HTTP request.
        Returns:
            Response or None: Returns a 413 JSON response if the size is over the limit, otherwise None.
        """
        client_ip = get_client_ip(request)
        url = request.url.path  # Secure attribute access, usually does not require handling.
        transfer_encoding = request.headers.get("transfer-encoding", "")
        is_chunked = "chunked" in transfer_encoding.lower()

        content_length = request.headers.get("content-length")

        # If Content-Length is provided and not chunked, check directly
        if content_length and not is_chunked:
            content_length = int(content_length)
            if content_length > self.max_body_size:
                logger.warning(f"[IP: {client_ip}] '{url}' {HTTPStatus.REQUEST_ENTITY_TOO_LARGE.value} "
                               f"Request body too large: {content_length} bytes, "
                               f"limit: {self.max_body_size} bytes")
                return JSONResponse(
                    status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                    content={"detail": f"Request body too large. "
                                       f"Maximum size: {self.max_body_size} bytes"}
                )
        return None

    def _handle_chunked_transfer(self, request: Request) -> None:
        """
        Handle chunked transfer encoding requests by wrapping the stream method to enforce size limits.
        Args:
            request (Request): The incoming HTTP request.
        """
        client_ip = get_client_ip(request)
        url = request.url.path  # Secure attribute access, usually does not require handling.
        transfer_encoding = request.headers.get("transfer-encoding", "")
        is_chunked = "chunked" in transfer_encoding.lower()

        # If it is a chunked transfer, monitor the size during reading
        if not is_chunked:
            return

        original_stream = request.stream()

        async def limited_stream():
            total_size = 0
            async for chunk in original_stream:
                total_size += len(chunk)
                if total_size > self.max_body_size:
                    logger.warning(f"[IP: {client_ip}] '{url}' {HTTPStatus.REQUEST_ENTITY_TOO_LARGE.value} "
                                   f"Chunked request body too large: {total_size} bytes, "
                                   f"limit: {self.max_body_size} bytes")
                    raise HTTPException(
                        status_code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                        detail=f"The request body is too large. "
                               f"Maximum size: {self.max_body_size} bytes"
                    )
                yield chunk

                request.stream = limited_stream


class ConcurrencyLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for limiting concurrent requests (production-grade implementation)"""
    def __init__(self, app: FastAPI, max_concurrent_requests: int = constants.MAX_CONCURRENT_REQUESTS) -> None:
        """
        Initialize the middleware with the given FastAPI app and maximum concurrent requests.
        Args:
            app (FastAPI): The FastAPI application.
            max_concurrent_requests (int): The maximum allowed concurrent requests. Default is 512.
        """
        super().__init__(app)
        self.max_concurrent_requests = max_concurrent_requests
        # Use semaphore for better concurrency control
        self.semaphore = asyncio.Semaphore(max_concurrent_requests)
        # Track active request count
        self.active_requests = 0
        self.lock = asyncio.Lock()

    async def dispatch(self, request: Request, call_next: callable) -> JSONResponse:
        """
        Dispatch the request and check the concurrent request limit.
        Args:
            request (Request): The incoming request.
            call_next (Callable): The next middleware or route handler.
        Returns:
            Response: The response from the next middleware or route handler.
        """
        # Check if maximum concurrent requests exceeded
        client_ip = get_client_ip(request)
        url = request.url.path  # Secure attribute access, usually does not require handling.
        async with self.lock:
            if self.active_requests >= self.max_concurrent_requests:
                logger.warning(
                    f"[IP: {client_ip}] '{url}' {HTTPStatus.TOO_MANY_REQUESTS.value} Too many concurrent requests: "
                    f"{self.active_requests}, limit: {self.max_concurrent_requests}")
                return JSONResponse(
                    status_code=HTTPStatus.TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Too many requests. "
                                  f"Maximum concurrent requests: {self.max_concurrent_requests}"}
                )
            self.active_requests += 1
            logger_service.debug(f"Request started, active requests: {self.active_requests}")

        try:
            # Use semaphore to control concurrency
            async with self.semaphore:
                try:
                    response = await call_next(request)
                    return response
                except Exception as e:
                    logger.error(f"[IP: {client_ip}] '{url}' {HTTPStatus.INTERNAL_SERVER_ERROR.value} "
                                 f"Error processing request: {e}")
                    return JSONResponse(
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        content={"detail": "An internal server error occurred."}
                    )
        finally:
            async with self.lock:
                self.active_requests -= 1
                logger_service.debug(f"Request finished, active requests: {self.active_requests}")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Time-window based rate limiting middleware (production-grade implementation)"""
    def __init__(self, app: FastAPI, config: RateLimitConfig = None) -> None:
        """
        Initialize the middleware with the given FastAPI app and rate limit configuration.

        Args:
            app (FastAPI): The FastAPI application.
            config (RateLimitConfig): The rate limit configuration. Default is a default RateLimitConfig instance.
        """
        super().__init__(app)
        self.config = config or RateLimitConfig()
        # Use sliding window algorithm to store request counts
        self.request_counts: Dict[str, Dict[str, Tuple[int, float]]] = defaultdict(dict)
        # Cleanup task for expired data
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_entries())
        self._counts_lock = asyncio.Lock()

    async def shutdown(self):
        """Cancel the cleanup task when the application is shutting down."""
        logger_service.info("Shutting down rate limit middleware")
        if self.cleanup_task and not self.cleanup_task.done():
            self.cleanup_task.cancel()
            logger_service.info("Cancelling rate limit middleware cleanup task")
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                logger_service.info("Rate limit middleware cleanup task has been cancelled.")

    async def dispatch(self, request: Request, call_next: callable) -> JSONResponse:
        """
        Dispatch the request and check the rate limit.
        Args:
            request (Request): The incoming request.
            call_next (Callable): The next middleware or route handler.
        Returns:
            JSONResponse: The response from the next middleware or route handler.
        """
        client_ip = get_client_ip(request)
        url = request.url.path  # Secure attribute access, usually does not require handling.
        # Check rate limit
        async with self._counts_lock:
            is_allowed, retry_after = self._check_rate_limit(client_ip)
            if not is_allowed:
                logger.warning(f"[IP: {client_ip}] '{url}' {HTTPStatus.TOO_MANY_REQUESTS.value} Rate limit exceeded")
                return JSONResponse(
                    status_code=HTTPStatus.TOO_MANY_REQUESTS,
                    content={
                        "detail": f"Rate limit exceeded",
                        "retry_after": retry_after
                    }
                )

            # Update count
            self._update_rate_limit(client_ip)

        response = await call_next(request)
        return response

    async def _cleanup_expired_entries(self) -> None:
        """Regularly clean up expired request count data to prevent memory leaks."""
        while True:
            try:
                logger_service.debug("Cleaning up expired rate limit entries")
                await self._remove_expired_data()
                await asyncio.sleep(self.config.cleanup_interval)
            except Exception as e:
                logger_service.error(f"An error occurred while clearing the request count: {e}")

    def _check_rate_limit(self, identifier: str) -> Tuple[bool, int]:
        """
        Check the rate limit for the given identifier.
        Args:
            identifier (str): The client identifier (usually IP address).
        Returns:
            Tuple[bool, int]: A tuple containing whether the request is allowed and the waiting time before retry.
        """
        current_time = time.time()

        # Check per-minute limit
        result = self._update_or_check_window(
            identifier, 'minute', current_time, 'requests_per_minute', is_check=True
        )
        if result and not result[0]:
            return result
        return True, 0

    async def _remove_expired_data(self) -> None:
        """Traverse all request counts and remove expired entries."""
        current_time = time.time()
        expired_keys = []

        for key in self.request_counts:
            count, timestamp = self.request_counts[key]
            if current_time - timestamp > CLEANUP_INTERVAL_SECONDS:
                expired_keys.append(key)
        async with self._counts_lock:
            for key in expired_keys:
                logger_service.debug(f"Deleting expired rate limit entry: {key}")
                del self.request_counts[key]

    def _update_or_check_window(
        self,
        identifier: str,
        window_type: str,  # 'minute'
        current_time: float,
        config_key: str,  # 'requests_per_minute'
        is_check: bool = False
    ) -> Tuple[Optional[bool], int]:
        """
        General method for checking or updating the request count within a specified time window.
        Args:
            identifier (str): Client identifier (e.g., IP address).
            window_type (str): Time window type, 'minute'.
            current_time (float): Current timestamp.
            config_key (str): Corresponding request limit key in the configuration.
            is_check (bool): Whether it is in check mode (True) or update mode (False).
        Returns:
            Tuple[Optional[bool], int]: If in check mode, returns (whether allowed, retry time); otherwise returns None.
        """
        key = f"{identifier}:{window_type}"
        window_seconds = MINUTE_SECONDS
        limit = getattr(self.config, config_key)

        if key in self.request_counts:
            count, timestamp = self.request_counts[key]
            if current_time - timestamp < window_seconds:
                if is_check and count >= limit:
                    retry_after = int(window_seconds - (current_time - timestamp)) + 1
                    return False, retry_after
                elif not is_check:
                    self.request_counts[key] = (count + 1, timestamp)
            else:
                if not is_check:
                    self.request_counts[key] = (1, current_time)
        else:
            if not is_check:
                self.request_counts[key] = (1, current_time)

        if is_check:
            return True, 0
        return None, 0

    def _update_rate_limit(self, identifier: str) -> None:
        """
        Update the rate limit counters for the given identifier.
        Args:
            identifier (str): The client identifier (usually IP address).
        """
        current_time = time.time()

        _ = self._update_or_check_window(identifier, 'minute',
                                         current_time, 'requests_per_minute')


class RequestTimeoutMiddleware(BaseHTTPMiddleware):
    """Middleware for setting a timeout on incoming requests (production-grade implementation)"""
    def __init__(self, app: FastAPI, request_timeout_in_sec: int = constants.REQUEST_TIMEOUT_IN_SEC):
        """
        Initialize the middleware with the given FastAPI app and request timeout in seconds.
        Args:
            app (FastAPI): The FastAPI application.
            request_timeout_in_sec (int): The maximum allowed time (in seconds) for a request to be processed.
                                          Default is defined by `constants.REQUEST_TIMEOUT_IN_SEC`.
        """
        super().__init__(app)
        self.timeout = request_timeout_in_sec

    async def dispatch(self, request: Request, call_next: callable) -> JSONResponse:
        """
        Dispatch the request and enforce the timeout limit.
        Args:
            request (Request): The incoming request.
            call_next (Callable): The next middleware or route handler.
        Returns:
            Response: The response from the next middleware or route handler if request is processed within the timeout.
        Raises:
            asyncio.TimeoutError: If the request processing exceeds the timeout.
        """
        client_ip = get_client_ip(request)
        url = request.url.path  # Secure attribute access, usually does not require handling.
        task = asyncio.create_task(call_next(request))
        try:
            # Using asyncio.wait_for to set a Timeout
            response = await asyncio.wait_for(task, timeout=self.timeout)
            return response
        except asyncio.TimeoutError:
            task.cancel()
            try:
                # Wait for the task cleanup to complete.
                await task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"[IP: {client_ip}] '{url}' {HTTPStatus.INTERNAL_SERVER_ERROR.value} "
                             f"Error during task cleanup after timeout: {e}")
                return JSONResponse(
                    status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                    content={"detail": "Request timeout and cleanup failed"}
                )

            logger.warning(f"[IP: {client_ip}] '{url}' {HTTPStatus.REQUEST_TIMEOUT.value} "
                           f"Request timeout after {self.timeout} seconds")
            return JSONResponse(
                status_code=HTTPStatus.REQUEST_TIMEOUT,
                content={"detail": f"Request timeout"}
            )
        except Exception as e:
            # If the task is still running, cancel it.
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                except Exception as cleanup_error:
                    logger.error(f"[IP: {client_ip}] '{url}' {HTTPStatus.INTERNAL_SERVER_ERROR.value} "
                                 f"Error during task cleanup after exception: {cleanup_error}")
                    return JSONResponse(
                        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                        content={"detail": "Request failed and cleanup failed"}
                    )

            logger.error(f"[IP: {client_ip}] '{url}' {HTTPStatus.INTERNAL_SERVER_ERROR.value} "
                         f"Error processing request: {e}")
            return JSONResponse(
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                content={"detail": "An internal server error occurred"}
            )
