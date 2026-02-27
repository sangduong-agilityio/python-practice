from fastapi import FastAPI
from .routes import user
from .routes import auth
from .core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

app.include_router(user.router)
app.include_router(auth.router)


@app.get("/")
def root():
    return {"message": "API is running"}
