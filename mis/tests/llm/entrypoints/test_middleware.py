#!/usr/bin/env python
# coding=utf-8
# Copyright (c) Huawei Technologies Co. Ltd. 2025. All rights reserved.
import asyncio
import unittest
from unittest.mock import Mock, AsyncMock, patch

import json
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.status import HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE, HTTP_200_OK

from mis.llm.entrypoints.middleware import (
    RequestTimeoutMiddleware,
    RequestHeaderSizeLimitMiddleware,
    RequestSizeLimitMiddleware,
    ConcurrencyLimitMiddleware,
    RateLimitMiddleware,
    RateLimitConfig
)


class TestRequestSizeLimitMiddleware(unittest.TestCase):
    """Test middleware for request body size limiting"""

    def setUp(self):
        """Set up test environment before each test method"""
        self.app = FastAPI()
        self.test_client = TestClient(self.app)

        # Add middleware
        self.app.add_middleware(RequestSizeLimitMiddleware, max_body_size=1024)  # 1KB limit

        @self.app.post("/test")
        async def test_endpoint(request: Request):
            body = await request.body()
            return {"size": len(body)}

    def test_request_within_limit(self):
        """Test request within the size limit"""
        # Send a request body smaller than the limit
        small_data = {"data": "x" * 512}  # About 512 bytes
        response = self.test_client.post("/test", json=small_data)
        self.assertEqual(response.status_code, 200)

    def test_request_exceeds_limit(self):
        """Test request exceeding the size limit"""
        # Send a request body larger than the limit
        large_data = {"data": "x" * 2048}  # About 2KB
        response = self.test_client.post("/test", json=large_data)
        self.assertEqual(response.status_code, 413)
        self.assertIn("Request body too large", response.json()["detail"])

    def test_chunked_transfer_within_limit(self):
        """Test chunked transfer within the limit"""
        # Simulate chunked transfer data
        def chunked_data():
            for i in range(4):  # 4 chunks, each 200 bytes = 800 bytes
                yield "x" * 200

        response = self.test_client.post(
            "/test",
            content="".join(chunked_data()),
            headers={"transfer-encoding": "chunked"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["size"], 800)

    def test_chunked_transfer_exceeds_limit(self):
        """Test chunked transfer exceeds the limit"""
        def chunked_data():
            for i in range(10):  # 10 chunks, each 200 bytes = 2000 bytes > 1024 bytes limit
                yield "x" * 200
        try:
            response = self.test_client.post(
                "/test",
                content="".join(chunked_data()),
                headers={"transfer-encoding": "chunked"}
            )
        except Exception as e:
            # Chunked transfer exceeding the limit will throw an exception, captured by middleware and returns 413
            self.assertIn("413", str(e))
            self.assertIn("Request body too large", str(e))

    def test_no_content_length_or_chunked(self):
        """Test requests without Content-Length and chunked transfer"""
        response = self.test_client.get("/test")  # GET requests usually have no request body
        self.assertEqual(response.status_code, 405)  # Method not allowed (only POST is defined)

    def test_exact_limit_size(self):
        """Test requests with exactly the limit size"""
        response = self.test_client.post(
            "/test",
            content="x" * 1024,  # Exactly 1KB
            headers={"content-length": "1024"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["size"], 1024)


class TestConcurrencyLimitMiddleware(unittest.IsolatedAsyncioTestCase):
    """Test middleware for concurrent request limiting"""

    def setUp(self):
        """Set up test environment before each test method"""
        self.app = FastAPI()
        self.max_concurrent_requests = 2
        self.middleware = ConcurrencyLimitMiddleware(self.app, max_concurrent_requests=self.max_concurrent_requests)
        # Add middleware with a limit of 2 concurrent requests
        self.app.add_middleware(ConcurrencyLimitMiddleware, max_concurrent_requests=self.max_concurrent_requests)

        # Create an endpoint that takes time to process for concurrency testing
        @self.app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(0.1)  # Simulate processing time
            return {"message": "success"}

        self.test_client = TestClient(self.app)

    def test_concurrent_requests_within_limit(self):
        """Test concurrent requests within the limit"""

        # Sending two concurrent requests should succeed
        async def make_requests():
            tasks = [asyncio.create_task(asyncio.sleep(0.01,
                                                        result=self.test_client.get("/slow"))) for _ in range(2)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            return responses

        responses = asyncio.run(make_requests())
        for response in responses:
            self.assertEqual(response.status_code, 200)

    async def test_concurrent_requests_exceed_limit(self):
        async def make_multiple_requests():
            tasks = []
            for _ in range(self.max_concurrent_requests + 2):
                task = asyncio.create_task(asyncio.to_thread(self.test_client.get, "/slow"))
                tasks.append(task)

            try:
                # Set a timeout for the gather operation
                responses = await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=1.0)
                return responses
            except asyncio.TimeoutError:
                return [asyncio.TimeoutError] * len(tasks)

        responses = await make_multiple_requests()

        successful_responses = 0
        limited_responses = 0

        for response in responses:
            if isinstance(response, asyncio.TimeoutError):
                continue

            if response.status_code == 200:
                successful_responses += 1
            elif response.status_code == 429:  # Too Many Requests
                limited_responses += 1

        self.assertEqual(successful_responses, self.max_concurrent_requests)
        self.assertGreaterEqual(limited_responses, 1)

    def test_exception_handling_in_call_next(self):
        mock_call_next = AsyncMock(side_effect=Exception("Test exception"))

        mock_request = Mock(spec=Request)
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        async def test_dispatch():
            try:
                await self.middleware.dispatch(mock_request, mock_call_next)
            except Exception:
                pass  # Exceptions will be re-thrown; only care about the state management within the middleware.

            # Even if an anomaly occurs, active_requests should be reset to 0.
            self.assertEqual(self.middleware.active_requests, 0)

        asyncio.run(test_dispatch())


class TestRateLimitMiddleware(unittest.IsolatedAsyncioTestCase):
    """Test middleware for rate limiting"""

    def setUp(self):
        """Set up test environment before each test method"""
        self.app = FastAPI()

        # Configure rate limits: max 2 requests per minute
        rate_limit_config = RateLimitConfig(
            requests_per_minute=2,
        )
        self.app.add_middleware(RateLimitMiddleware, config=rate_limit_config)

        self.test_client = TestClient(self.app)

        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

    @patch('mis.llm.entrypoints.middleware.get_client_ip')
    def test_rate_limit_per_minute(self, mock_get_client_ip):
        """Test per-minute rate limiting"""
        # Mock client IP
        mock_get_client_ip.return_value = "127.0.0.1"

        # Send two requests, both should succeed
        response1 = self.test_client.get("/test")
        response2 = self.test_client.get("/test")

        self.assertEqual(response1.status_code, 200)
        self.assertEqual(response2.status_code, 200)

        # Third request should be rate limited
        response3 = self.test_client.get("/test")
        self.assertEqual(response3.status_code, 429)
        self.assertIn("Rate limit exceeded", response3.json()["detail"])

    async def test_check_rate_limit_allowed(self):
        """Test rate limit check that allows request"""
        middleware = RateLimitMiddleware(FastAPI())
        middleware.config = RateLimitConfig(requests_per_minute=2)

        # Mock a client identifier
        identifier = "test_client"

        # Check rate limit, should allow
        is_allowed, retry_after = middleware._check_rate_limit(identifier)
        self.assertTrue(is_allowed)
        self.assertEqual(retry_after, 0)

    async def test_update_rate_limit(self):
        """Test updating rate limit counters"""
        middleware = RateLimitMiddleware(FastAPI())
        middleware.config = RateLimitConfig(requests_per_minute=2)

        identifier = "test_client"

        # Update rate limit counters
        middleware._update_rate_limit(identifier)

        # Check that counters are correctly updated
        self.assertIn(f"{identifier}:minute", middleware.request_counts)
        self.assertEqual(middleware.request_counts[f"{identifier}:minute"][0], 1)


class FastAPIAppWithTimeout:
    """
    FastAPI application example with timeout handling
    """

    def __init__(self, request_timeout_in_sec: int = 1):
        self.app = FastAPI()
        self.app.add_middleware(RequestTimeoutMiddleware, request_timeout_in_sec=request_timeout_in_sec)

        @self.app.get("/slow")
        async def slow_endpoint():
            await asyncio.sleep(1.5)  # Simulate a slow response
            return {"message": "Hello World"}

        @self.app.get("/fast")
        async def fast_endpoint():
            return {"message": "Hello World"}


class TestRequestTimeoutMiddleware(unittest.TestCase):
    """
    Test class for request timeout middleware
    """

    def setUp(self):
        """
        Test initialization
        """
        self.fast_app = FastAPIAppWithTimeout(request_timeout_in_sec=1)
        self.client = TestClient(self.fast_app.app)

    def test_fast_request_not_timeout(self):
        """
        Test that a fast request does not timeout
        """
        response = self.client.get("/fast")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Hello World"})

    def test_slow_request_timeout(self):
        """
        Test that a slow request times out
        """
        response = self.client.get("/slow")
        self.assertEqual(response.status_code, 408)
        self.assertEqual(response.json(), {'detail': 'Request timeout'})

    def test_middleware_initialization(self):
        """
        Test middleware initialization
        """
        app = FastAPI()
        middleware = RequestTimeoutMiddleware(app, request_timeout_in_sec=5)
        self.assertEqual(middleware.timeout, 5.0)

    async def test_dispatch_with_timeout_error(self):
        """
        Test dispatch method handling timeout error
        """
        app = FastAPI()
        middleware = RequestTimeoutMiddleware(app, request_timeout_in_sec=0)

        # Simulate a call_next function that will timeout
        async def slow_call_next(request):
            await asyncio.sleep(1)
            return JSONResponse(content={"message": "OK"})

        # Create a mock request
        request = Mock(spec=Request)

        # Execute dispatch method
        response = await middleware.dispatch(request, slow_call_next)

        # Verify timeout response is returned
        self.assertEqual(response.status_code, 408)
        self.assertEqual(response.body, b'{"detail":"Request timeout"}')

    async def test_dispatch_without_timeout(self):
        """
        Test dispatch method under normal conditions
        """
        app = FastAPI()
        middleware = RequestTimeoutMiddleware(app, request_timeout_in_sec=1)

        # Simulate a normal call_next function
        async def normal_call_next(request):
            return JSONResponse(content={"message": "OK"})

        # Create a mock request
        request = Mock(spec=Request)

        # Execute dispatch method
        response = await middleware.dispatch(request, normal_call_next)

        # Verify normal response is returned
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.body, b'{"message":"OK"}')


class TestRequestTimeoutIntegration(unittest.TestCase):
    """
    Integration test class for request timeout
    """

    def setUp(self):
        """
        Test initialization with longer timeout to ensure test stability
        """
        self.fast_app = FastAPIAppWithTimeout(request_timeout_in_sec=1)
        self.client = TestClient(self.fast_app.app)

    def test_multiple_fast_requests(self):
        """
        Test that multiple fast requests are processed normally
        """
        for i in range(5):
            response = self.client.get("/fast")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"message": "Hello World"})

    def test_mixed_requests(self):
        """
        Test mixed fast and slow requests
        """
        # Send a fast request first
        fast_response = self.client.get("/fast")
        self.assertEqual(fast_response.status_code, 200)

        # Send a slow request, which should timeout
        slow_response = self.client.get("/slow")
        self.assertEqual(slow_response.status_code, 408)

        # Send another fast request to confirm the service is working
        fast_response2 = self.client.get("/fast")
        self.assertEqual(fast_response2.status_code, 200)


class TestRequestHeaderSizeLimitMiddleware(unittest.TestCase):
    """Test the request header size limit middleware"""
    def setUp(self):
        """Initialize the test environment"""
        self.app = FastAPI()
        self.test_client = TestClient(self.app)

        # Add middleware, set the maximum request header size to 1024 bytes
        self.app.add_middleware(RequestHeaderSizeLimitMiddleware, max_header_size=1024)

        @self.app.get("/test")
        async def test_endpoint():
            return {"message": "success"}

    def test_request_with_small_headers(self):
        """Test request headers within the limit"""
        response = self.test_client.get("/test")
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {"message": "success"})

    def test_request_with_large_headers(self):
        """Test request headers exceeding the limit"""
        # Construct a request with a large number of headers
        headers = {
            "X-Test-Header-1": "x" * 500,
            "X-Test-Header-2": "x" * 500,
            "X-Test-Header-3": "x" * 100,
        }

        # Total header size exceeds 1024 bytes
        response = self.test_client.get("/test", headers=headers)
        self.assertEqual(response.status_code, HTTP_431_REQUEST_HEADER_FIELDS_TOO_LARGE)
        self.assertIn("Request headers too large", response.json()["detail"])

    def test_request_with_exact_limit_headers(self):
        """Test request headers exactly at the limit"""
        # Set the maximum request header size to 1024 bytes.
        max_header_size = 1024
        #   #example: Headers({'host': 'testserver', 'accept': '*/*', 'accept-encoding': 'gzip, deflate',
        #   #'connection': 'keep-alive', 'user-agent': 'testclient', 'x-test-header': 'xx...x'})
        header_reserved_size = (len('host') + len('testserver') + len('accept') + len('*/*') +
                                len('accept-encoding') + len('gzip, deflate') + len('connection') +
                                len('keep-alive') + len('user-agent') + len('testclient') + len(': ') * 6)
        header_name = "X-Test-Header"
        header_value_length = max_header_size - len(header_name.encode('utf-8')) - header_reserved_size
        header_value = "x" * header_value_length

        headers = {
            header_name: header_value
        }

        response = self.test_client.get("/test", headers=headers)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(response.json(), {"message": "success"})

    def test_request_with_invalid_header_encoding(self):
        """Test the case where request header parsing fails"""
        # Simulate a request object
        mock_request = Mock(spec=Request)
        mock_request.headers.items.side_effect = Exception("Invalid header encoding")  # Simulate parsing failure

        # Simulate call_next (normal return)
        mock_call_next = AsyncMock(return_value=JSONResponse(content={"message": "success"}, status_code=200))

        # Simulate logger
        with patch("mis.llm.entrypoints.middleware.op_logger") as mock_logger:
            # Simulate get_client_ip to avoid accessing request.headers
            with patch("mis.llm.entrypoints.middleware.get_client_ip", return_value="127.0.0.1"):
                # Instantiate middleware
                middleware = RequestHeaderSizeLimitMiddleware(FastAPI(), max_header_size=1024)

                # Call dispatch method
                response = asyncio.run(middleware.dispatch(mock_request, mock_call_next))

                # Verify response
                self.assertEqual(response.status_code, 400)
                response_content = response.body.decode("utf-8")
                response_dict = json.loads(response_content)
                self.assertIn("Error parsing request headers", response_dict["detail"])

                # Verify if the log is recorded
                mock_logger.error.assert_called()

    def test_middleware_initialization(self):
        """Test middleware initialization"""
        app = FastAPI()
        middleware = RequestHeaderSizeLimitMiddleware(app, max_header_size=2048)
        self.assertEqual(middleware.max_header_size, 2048)

    def test_invalid_app_or_max_header_size(self):
        """Test exceptions when invalid parameters are passed"""
        with self.assertRaises(ValueError):
            RequestHeaderSizeLimitMiddleware(None, max_header_size=1024)

        with self.assertRaises(TypeError):
            RequestHeaderSizeLimitMiddleware(FastAPI(), max_header_size="invalid")


if __name__ == '__main__':
    unittest.main()
