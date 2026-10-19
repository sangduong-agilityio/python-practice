"""
app/api/v1/endpoints/tags.py
-----------------------------
Tag management and task-tag relationship endpoints.
"""

from fastapi import APIRouter, status

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.tag import TagCreate, TagOut
from app.schemas.task import TaskOut
from app.services.tag_service import TagService
from app.services.task_service import TaskService

router = APIRouter(tags=["Tags"])


@router.post(
    "/tags",
    response_model=TagOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a tag",
)
async def create_tag(
    data: TagCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> TagOut:
    """
    Create a new tag with a name and optional hex color.

    Tags are global — any user can create them and attach them to tasks.
    """
    service = TagService(db)
    return await service.create(data)  # type: ignore[return-value]


@router.get(
    "/tags",
    response_model=list[TagOut],
    summary="List all tags",
)
async def list_tags(
    current_user: CurrentUser,
    db: DbSession,
) -> list[TagOut]:
    """Return all available tags, sorted alphabetically."""
    service = TagService(db)
    return await service.list_all()  # type: ignore[return-value]


@router.post(
    "/tasks/{task_id}/tags/{tag_id}",
    response_model=TaskOut,
    summary="Attach a tag to a task",
)
async def add_tag_to_task(
    task_id: int,
    tag_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskOut:
    """Attach an existing tag to a task (project owner only)."""
    service = TaskService(db)
    return await service.add_tag(task_id, tag_id, current_user)  # type: ignore[return-value]


@router.delete(
    "/tasks/{task_id}/tags/{tag_id}",
    response_model=TaskOut,
    summary="Remove a tag from a task",
)
async def remove_tag_from_task(
    task_id: int,
    tag_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskOut:
    """Detach a tag from a task (project owner only)."""
    service = TaskService(db)
    return await service.remove_tag(task_id, tag_id, current_user)  # type: ignore[return-value]
