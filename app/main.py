"""
app/main.py
-----------
Application factory — the entry point of the FastAPI app.

This file:
  1. Creates the FastAPI app instance with metadata.
  2. Registers middleware (CORS, logging).
  3. Mounts the API router under /api/v1.
  4. Adds a global exception handler for unexpected errors.
  5. Defines the lifespan context (startup / shutdown hooks).
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.middleware.logging import RequestLoggingMiddleware

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan — startup and shutdown logic
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Code before `yield` runs at startup.
    Code after `yield` runs at shutdown.

    This replaces the older @app.on_event("startup") pattern.
    We use it to log that the app is ready. In a real app you might
    also warm up caches or check external service connectivity here.
    """
    logger.info("🚀 %s v%s starting up...", settings.APP_TITLE, settings.APP_VERSION)
    yield
    logger.info("🛑 %s shutting down.", settings.APP_TITLE)


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Using a factory function (instead of a module-level `app = FastAPI()`)
    makes testing easier — you can call create_app() with different settings.

    Returns:
        Configured FastAPI instance.
    """
    app = FastAPI(
        title=settings.APP_TITLE,
        version=settings.APP_VERSION,
        description="A production-ready Task Management REST API built with FastAPI.",
        docs_url="/docs",          # Swagger UI
        redoc_url="/redoc",        # ReDoc UI
        lifespan=lifespan,
    )

    # --- CORS Middleware ---
    # Must be added BEFORE other middleware so preflight OPTIONS requests
    # are handled correctly before they reach other layers.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],   # Allow all HTTP methods
        allow_headers=["*"],   # Allow all headers (including Authorization)
    )

    # --- Request Logging Middleware ---
    app.add_middleware(RequestLoggingMiddleware)

    # --- API Router ---
    # All endpoints are prefixed with /api/v1, e.g. /api/v1/auth/register
    app.include_router(api_router, prefix="/api/v1")

    # --- Global Exception Handler ---
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Catch any unhandled exception and return a clean 500 response.

        NEVER expose the raw exception message or stack trace to the client —
        that would leak internal implementation details to potential attackers.
        Log it server-side instead so developers can diagnose it.
        """
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An internal server error occurred. Please try again later."},
        )

    # --- Health Check ---
    @app.get("/health", tags=["Health"], summary="Health check")
    async def health_check() -> dict:
        """Simple endpoint to verify the API is running. Used by load balancers."""
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


# Create the app instance — Uvicorn imports this
app = create_app()
