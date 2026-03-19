from contextlib import asynccontextmanager
from fastapi import FastAPI
from .routes import user, auth, task, project
from .core.config import settings
from .db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Create tables
    await create_db_and_tables()
    yield
    # Shutdown: Can add cleanup code here if needed


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(task.router)
app.include_router(project.router)


@app.get("/")
def root():
    return {"message": "API is running"}
