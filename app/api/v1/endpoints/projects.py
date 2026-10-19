"""
app/api/v1/endpoints/projects.py
----------------------------------
Project CRUD endpoints — all require authentication.
"""

from fastapi import APIRouter, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
)
async def create_project(
    data: ProjectCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectOut:
    """Create a project owned by the authenticated user."""
    service = ProjectService(db)
    return await service.create(data, owner=current_user)  # type: ignore[return-value]


@router.get(
    "",
    response_model=list[ProjectOut],
    summary="List your projects",
)
async def list_projects(
    current_user: CurrentUser,
    db: DbSession,
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    limit: int = Query(default=20, ge=1, le=100, description="Max records to return"),
) -> list[ProjectOut]:
    """
    Return a paginated list of your projects, newest first.

    Use `skip` and `limit` for pagination:
    - Page 1: skip=0, limit=20
    - Page 2: skip=20, limit=20
    """
    service = ProjectService(db)
    return await service.list_for_user(current_user, skip=skip, limit=limit)  # type: ignore[return-value]


@router.get(
    "/{project_id}",
    response_model=ProjectOut,
    summary="Get a single project",
)
async def get_project(
    project_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectOut:
    """Fetch a single project by its ID."""
    service = ProjectService(db)
    project = await service.get_or_404(project_id)
    # Anyone can view a project for now; restrict to members in a real app
    return project  # type: ignore[return-value]


@router.put(
    "/{project_id}",
    response_model=ProjectOut,
    summary="Update a project (owner only)",
)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> ProjectOut:
    """Update a project's title or description. Only the project owner can do this."""
    service = ProjectService(db)
    return await service.update(project_id, data, current_user)  # type: ignore[return-value]


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project (owner only)",
)
async def delete_project(
    project_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """
    Permanently delete a project and all its tasks.
    Only the project owner can delete it.
    Returns 204 No Content on success.
    """
    service = ProjectService(db)
    await service.delete(project_id, current_user)
