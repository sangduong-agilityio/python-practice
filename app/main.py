"""
Application entry point.

create_app() is a factory function rather than a module-level app = FastAPI()
so tests can import create_app and call it with different settings without
the side effects of module-level code running at import time.
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from app.api.v1.router import v1_router
from app.core.cache import get_redis_client
from app.core.config import settings
from app.core.exceptions import (
    AuthenticationFailedException,
    InvalidFieldException,
    PermissionDeniedException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from app.core.logger import setup_logging
from app.core.rate_limit import limiter
from app.db.session import engine
from app.middleware.logging import LoggingMiddleware

log = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup")
    yield
    log.info("shutdown")


def create_app() -> FastAPI:
    # Initialize structured logging before the app starts handling requests.
    # (Idempotent; safe to call multiple times in tests.)
    setup_logging()
    app = FastAPI(
        title="Task Management API",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # CORSMiddleware must be registered before any custom middleware
    # so it can handle preflight OPTIONS requests before they hit our code.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(o).rstrip("/") for o in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(LoggingMiddleware)

    @app.exception_handler(ResourceNotFoundException)
    async def not_found_handler(_: Request, exc: ResourceNotFoundException) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": exc.message})

    @app.exception_handler(PermissionDeniedException)
    async def forbidden_handler(_: Request, exc: PermissionDeniedException) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"detail": exc.message})

    @app.exception_handler(AuthenticationFailedException)
    async def auth_failed_handler(_: Request, exc: AuthenticationFailedException) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": exc.message},
            headers={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(ResourceAlreadyExistsException)
    async def conflict_handler(_: Request, exc: ResourceAlreadyExistsException) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": exc.message})

    @app.exception_handler(InvalidFieldException)
    async def invalid_field_handler(_: Request, exc: InvalidFieldException) -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": exc.message})

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Invalid input data", "errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled(_: Request, exc: Exception) -> JSONResponse:
        # Log the real error server-side, return a generic message to the client.
        log.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )

    app.include_router(v1_router, prefix="/api/v1")

    @app.get("/health", tags=["health"])
    async def health() -> dict:
        # Check DB
        db_status = "ok"
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            log.error("health_db_failed", error=str(e))
            db_status = "failed"

        # Check Redis
        redis_status = "ok"
        try:
            client = get_redis_client()
            await client.ping()
        except Exception as e:
            log.error("health_redis_failed", error=str(e))
            redis_status = "failed"

        status_code = status.HTTP_200_OK if db_status == "ok" and redis_status == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ok" if status_code == status.HTTP_200_OK else "degraded",
                "components": {
                    "database": db_status,
                    "redis": redis_status,
                }
            }
        )

    return app


app = create_app()
