import time
import uuid
import structlog
from structlog.contextvars import bind_contextvars, clear_contextvars

log = structlog.get_logger("api.access")

class LoggingMiddleware:
    """
    Pure ASGI Middleware for logging and security headers.
    Avoids BaseHTTPMiddleware to prevent ExceptionGroup/TaskGroup issues.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        clear_contextvars()
        request_id = uuid.uuid4().hex
        bind_contextvars(request_id=request_id)
        
        start_time = time.perf_counter()
        
        # Helper to inject headers in the response
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                
                # Add X-Request-ID
                headers.append((b"x-request-id", request_id.encode()))
                
                # Add Security Headers
                headers.append((b"strict-transport-security", b"max-age=31536000; includeSubDomains"))
                headers.append((b"x-content-type-options", b"nosniff"))
                headers.append((b"x-frame-options", b"DENY"))
                headers.append((b"x-xss-protection", b"1; mode=block"))
                
                message["headers"] = headers
            
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as exc:
            duration = (time.perf_counter() - start_time) * 1000
            log.error(
                "request_failed",
                method=scope["method"],
                path=scope["path"],
                duration_ms=round(duration, 2),
                error=str(exc)
            )
            raise exc from None
        finally:
            # Note: Successful completion logging happens in the ASGI flow or can be done here
            # for simple cases. However, since we wrapped 'send', it's already robust.
            pass
