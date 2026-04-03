from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# Allowed Frontend Origins
origins = [
    "http://localhost",
    "http://localhost:3000",   # Default for React/Next.js apps
    "http://localhost:5173",   # Default for Vite (Vue/React)
    "http://localhost:8080",
]

# Configure CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # Allowed origins
    allow_credentials=True,      # Allow cross-origin cookies and Authorization headers
    allow_methods=["*"],         # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],         # Allow all HTTP headers
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "API is running"}
