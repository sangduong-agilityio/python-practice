from fastapi import APIRouter

from app.api.v1.endpoints import auth, chat, projects, tags, tasks, users

v1_router = APIRouter()

v1_router.include_router(auth.router)
v1_router.include_router(users.router)
v1_router.include_router(projects.router)
v1_router.include_router(tasks.router)
v1_router.include_router(tags.router)
v1_router.include_router(chat.router)
