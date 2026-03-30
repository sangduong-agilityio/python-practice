from contextlib import asynccontextmanager
from fastapi import FastAPI

from .api.v1.router import api_router
from . import models
from .core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # DB initialization is now handled via Alembic Migrations
    yield
    # Shutdown: Can add cleanup code here if needed


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "API is running"}
