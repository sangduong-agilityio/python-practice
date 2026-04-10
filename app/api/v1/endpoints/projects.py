"""
Project endpoints -- CRUD operations for projects.
"""

from fastapi import APIRouter, Query, status

from app.core.cache import cache_delete_pattern, cache_get, cache_set
from app.core.dependencies import CurrentUser, DbSession
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])

_CACHE_PREFIX = "projects:user"


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(data: ProjectCreate, current_user: CurrentUser, db: DbSession) -> ProjectResponse:
    """Create a new project owned by the current user."""
    project = await ProjectService(db).create(data, current_user)
    await cache_delete_pattern(f"{_CACHE_PREFIX}:{current_user.id}:*")
    return project


@router.get("", response_model=list[ProjectResponse])
async def list_projects(
    current_user: CurrentUser,
    db: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[ProjectResponse]:
    """List projects owned by the current user with pagination."""
    cache_key = f"{_CACHE_PREFIX}:{current_user.id}:skip={skip}:limit={limit}"
    cached = await cache_get(cache_key)
    if cached is not None:
        return cached

    projects = await ProjectService(db).list_for_user(current_user, skip=skip, limit=limit)
    serialised = [ProjectResponse.model_validate(p).model_dump(mode="json") for p in projects]
    await cache_set(cache_key, serialised)
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, current_user: CurrentUser, db: DbSession) -> ProjectResponse:
    """Get a single project by ID."""
    service = ProjectService(db)
    project = await service.get_or_404(project_id)
    service.assert_owner(project, current_user)
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int, data: ProjectUpdate, current_user: CurrentUser, db: DbSession
) -> ProjectResponse:
    """Update a project's fields."""
    project = await ProjectService(db).update(project_id, data, current_user)
    await cache_delete_pattern(f"{_CACHE_PREFIX}:{current_user.id}:*")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: int, current_user: CurrentUser, db: DbSession) -> None:
    """Permanently delete a project and all its tasks."""
    await ProjectService(db).delete(project_id, current_user)
    await cache_delete_pattern(f"{_CACHE_PREFIX}:{current_user.id}:*")
