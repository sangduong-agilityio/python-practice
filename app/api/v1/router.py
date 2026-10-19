"""
app/api/v1/router.py
---------------------
Aggregates all v1 endpoint routers into a single APIRouter.

This file is the "table of contents" for the API.
Adding a new feature means importing its router here.
`app/main.py` mounts this router under the `/api/v1` prefix.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, projects, tasks, tags

# The v1 router acts as a namespace — all routes registered here
# will be prefixed with `/api/v1` when mounted in main.py
api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(tasks.router)
api_router.include_router(tags.router)
