from fastapi import FastAPI
from .routes import user, auth, task, project
from .core.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

app.include_router(user.router)
app.include_router(auth.router)
app.include_router(task.router)
app.include_router(project.router)


@app.get("/")
def root():
    return {"message": "API is running"}
