"""
app/middleware/logging.py
--------------------------
Request/response logging middleware.

Middleware wraps every incoming HTTP request. This middleware:
  1. Logs the method, path, and client IP when a request arrives.
  2. Times how long the route handler takes.
  3. Logs the response status code and duration when the response is sent.

This gives you an audit trail for every API call without adding
any code to individual route handlers.
"""

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("api.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Starlette/FastAPI middleware that logs every request and response.

    Inheriting from BaseHTTPMiddleware requires implementing `dispatch`,
    which receives the request and a `call_next` function that runs
    the actual route handler.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Intercept the request, log it, run the handler, log the response.

        Args:
            request  : The incoming HTTP request.
            call_next: Callable that executes the matched route handler.

        Returns:
            The HTTP response from the route handler.
        """
        start_time = time.perf_counter()

        # Log incoming request
        logger.info(
            "→ %s %s | client=%s",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
        )

        # Run the actual route handler
        response = await call_next(request)

        # Calculate processing duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "← %s %s | status=%d | %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        # Add processing time to response headers (useful for frontend debugging)
        response.headers["X-Process-Time-Ms"] = f"{duration_ms:.1f}"

        return response
