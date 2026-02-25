from fastapi import FastAPI
from fastapi_training.practice_one.app.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)


@app.get("/")
def root():
    return {"message": "API is running"}
