"""
Request logging middleware.

Logs method, path, status, and response time on every request.
Keeping this in middleware rather than inside each handler means
we never forget to log a new endpoint.
"""

import time
import uuid

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from structlog.contextvars import bind_contextvars, clear_contextvars

log = structlog.get_logger("api.access")


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        # Reset contextvars for each request to avoid leaking data between requests
        clear_contextvars()
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        # Bind the request ID to the contextvars so it gets included in all log messages for this request
        bind_contextvars(request_id=request_id)
        # Also store the request ID in the request state so it can be accessed in handlers if needed
        request.state.request_id = request_id
        # Log the incoming request with method and path
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as e:
            duration_ms = (time.perf_counter() - start) * 1000
            log.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                error=str(e),
            )
            raise

        duration_ms = (time.perf_counter() - start) * 1000

        log.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2)
        )
        response.headers["X-Request-ID"] = request_id
        return response
