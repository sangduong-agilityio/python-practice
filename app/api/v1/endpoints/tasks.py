"""
app/api/v1/endpoints/tasks.py
------------------------------
Task CRUD, status change, and assignment endpoints.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.models.task import TaskPriority, TaskStatus
from app.repositories.user_repository import UserRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.task import TaskAssignUpdate, TaskCreate, TaskOut, TaskStatusUpdate, TaskUpdate
from app.services.email_service import send_task_assigned_email
from app.services.task_service import TaskService

router = APIRouter(tags=["Tasks"])


# ---------------------------------------------------------------------------
# Tasks nested under a project
# ---------------------------------------------------------------------------

@router.post(
    "/projects/{project_id}/tasks",
    response_model=TaskOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task in a project",
)
async def create_task(
    project_id: int,
    data: TaskCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskOut:
    """Create a new task inside the specified project (owner only)."""
    service = TaskService(db)
    return await service.create(project_id, data, current_user)  # type: ignore[return-value]


@router.get(
    "/projects/{project_id}/tasks",
    response_model=list[TaskOut],
    summary="List tasks in a project",
)
async def list_tasks(
    project_id: int,
    current_user: CurrentUser,
    db: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    status_filter: str | None = Query(default=None, alias="status"),
    priority_filter: str | None = Query(default=None, alias="priority"),
) -> list[TaskOut]:
    """
    List all tasks in a project with optional filters.

    Query params:
    - **status**: Filter by status (case-insensitive: todo | in_progress | done)
    - **priority**: Filter by priority (case-insensitive: low | medium | high)
    """
    parsed_status: TaskStatus | None = None
    if status_filter:
        normalized_status = status_filter.strip().lower()
        try:
            parsed_status = TaskStatus(normalized_status)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid status '{status_filter}'. Allowed values: {[s.value for s in TaskStatus]}",
            )

    parsed_priority: TaskPriority | None = None
    if priority_filter:
        normalized_priority = priority_filter.strip().lower()
        try:
            parsed_priority = TaskPriority(normalized_priority)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid priority '{priority_filter}'. Allowed values: {[p.value for p in TaskPriority]}",
            )

    service = TaskService(db)
    return await service.list_for_project(  # type: ignore[return-value]
        project_id,
        current_user,
        skip=skip,
        limit=limit,
        status_filter=parsed_status,
        priority_filter=parsed_priority,
    )


# ---------------------------------------------------------------------------
# Individual task operations
# ---------------------------------------------------------------------------

@router.get(
    "/tasks/{task_id}",
    response_model=TaskOut,
    summary="Get a single task",
)
async def get_task(
    task_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskOut:
    """Fetch a single task by its ID."""
    service = TaskService(db)
    return await service.get_or_404(task_id)  # type: ignore[return-value]


@router.put(
    "/tasks/{task_id}",
    response_model=TaskOut,
    summary="Update a task",
)
async def update_task(
    task_id: int,
    data: TaskUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskOut:
    """Update task fields. Only the project owner can modify tasks."""
    service = TaskService(db)
    return await service.update(task_id, data, current_user)  # type: ignore[return-value]


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
async def delete_task(
    task_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Permanently delete a task (project owner only)."""
    service = TaskService(db)
    await service.delete(task_id, current_user)


@router.patch(
    "/tasks/{task_id}/status",
    response_model=TaskOut,
    summary="Update task status",
)
async def change_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskOut:
    """
    Change only the status of a task.
    Useful for Kanban-style drag-and-drop without sending the whole task object.
    """
    service = TaskService(db)
    return await service.change_status(task_id, data.status, current_user)  # type: ignore[return-value]


@router.patch(
    "/tasks/{task_id}/assign",
    response_model=TaskOut,
    summary="Assign or unassign a task",
)
async def assign_task(
    task_id: int,
    data: TaskAssignUpdate,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    db: DbSession,
) -> TaskOut:
    """
    Assign a task to a user, or unassign (set assignee_id to null).
    Sends a notification email to the assignee in the background.
    """
    service = TaskService(db)
    task = await service.assign(task_id, data.assignee_id, current_user)

    # Send assignment notification email in the background
    if data.assignee_id is not None:
        user_repo = UserRepository(db)
        project_repo = ProjectRepository(db)
        assignee = await user_repo.get_by_id(data.assignee_id)
        project = await project_repo.get_by_id(task.project_id)
        if assignee and project:
            background_tasks.add_task(
                send_task_assigned_email,
                assignee.email,
                assignee.username,
                task.title,
                project.title,
            )

    return task  # type: ignore[return-value]
