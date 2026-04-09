"""
Task business logic.

Tasks are scoped to projects, so every operation first verifies
the project exists and the caller owns it before touching the task.
"""

import uuid

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.repositories import task_repository, user_repository
from app.repositories.tag_repository import TagRepository
from app.schemas.task import (
    TaskAssignUpdate,
    TaskCreate,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services import project_service
from app.services.email_service import send_task_assigned


async def get_or_404(db: AsyncSession, task_id: uuid.UUID) -> Task:
    """Fetch a task by ID or raise a 404 error if not found.

    Args:
        db: Database session.
        task_id: UUID of the task.

    Returns:
        The matched Task instance.

    Raises:
        HTTPException 404: If no task with the given ID exists.
    """
    task = await task_repository.get_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


async def _assert_project_access(db: AsyncSession, task: Task, user: User) -> None:
    """Verify that a user has access to a given task via its parent project.

    Tasks inherit access control from their project. This function ensures
    the user is the owner of the project containing the task.

    Args:
        db: Database session.
        task: The Task instance being accessed.
        user: The User instance attempting access.

    Raises:
        HTTPException 403: If the user is not the owner of the parent project.
    """
    # Reuse the project-level ownership check rather than duplicating it here.
    project = await project_service.get_or_404(db, task.project_id)
    project_service.assert_owner(project, user)


async def create(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: TaskCreate,
    current_user: User,
) -> Task:
    """Create a new task under a specific project.

    Args:
        db: Database session.
        project_id: UUID of the project the task belongs to.
        data: Validation schema for the new task.
        current_user: The authenticated User initiating the request.

    Returns:
        The created Task instance.

    Raises:
        HTTPException 403: If the current user does not own the project.
        HTTPException 404: If the project does not exist.
    """
    project = await project_service.get_or_404(db, project_id)
    project_service.assert_owner(project, current_user)

    task = Task(
        title=data.title,
        description=data.description,
        priority=data.priority,
        due_date=data.due_date,
        project_id=project.id,
    )
    return await task_repository.create(db, task)


async def list_for_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    current_user: User,
    status_filter: TaskStatus | None = None,
    priority_filter: TaskPriority | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Task]:
    """Retrieve a paginated list of tasks for a project, optionally filtered.

    Args:
        db: Database session.
        project_id: UUID of the project.
        current_user: The User requesting the list.
        status_filter: Optional status to filter by.
        priority_filter: Optional priority to filter by.
        skip: Pagination offset.
        limit: Maximum number of tasks to return.

    Returns:
        A list of Task instances belonging to the project.
    """
    project = await project_service.get_or_404(db, project_id)
    project_service.assert_owner(project, current_user)
    return await task_repository.get_by_project(
        db, project_id,
        status=status_filter,
        priority=priority_filter,
        skip=skip,
        limit=limit,
    )


async def update(
    db: AsyncSession,
    task_id: uuid.UUID,
    data: TaskUpdate,
    current_user: User,
) -> Task:
    """Update general fields of a task.

    Args:
        db: Database session.
        task_id: UUID of the task.
        data: Schema containing fields to update.
        current_user: Authenticated User initiating the request.

    Returns:
        The updated Task instance.
    """
    task = await get_or_404(db, task_id)
    await _assert_project_access(db, task, current_user)
    # exclude_unset rather than exclude_none so callers can explicitly
    # clear a nullable field by sending null in the request body.
    return await task_repository.update(db, task, data.model_dump(exclude_unset=True))


async def change_status(
    db: AsyncSession,
    task_id: uuid.UUID,
    data: TaskStatusUpdate,
    current_user: User,
) -> Task:
    task = await get_or_404(db, task_id)
    await _assert_project_access(db, task, current_user)
    return await task_repository.update(db, task, {"status": data.status})


async def assign(
    db: AsyncSession,
    task_id: uuid.UUID,
    data: TaskAssignUpdate,
    current_user: User,
    background_tasks: BackgroundTasks,
) -> Task:
    """Assign or unassign a user to a task.

    If assigned to a new user, an email notification is pushed to a background worker.

    Args:
        db: Database session.
        task_id: UUID of the task.
        data: Contains the assignee_id (or None to unassign).
        current_user: Authenticated User initiating the request.
        background_tasks: BackgroundTasks for email dispatcher.

    Returns:
        The updated Task instance.
    """
    task = await get_or_404(db, task_id)
    await _assert_project_access(db, task, current_user)

    if data.assignee_id is not None:
        assignee = await user_repository.get_by_id(db, data.assignee_id)
        if assignee is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignee not found")
        background_tasks.add_task(send_task_assigned, assignee.email, assignee.username, task.title)

    return await task_repository.update(db, task, {"assignee_id": data.assignee_id})


async def delete(db: AsyncSession, task_id: uuid.UUID, current_user: User) -> None:
    """Delete a task permanently.

    Args:
        db: Database session.
        task_id: UUID of the task.
        current_user: Authenticated User initiating the request.
    """
    task = await get_or_404(db, task_id)
    await _assert_project_access(db, task, current_user)
    await task_repository.delete(db, task)


async def attach_tag(
    db: AsyncSession,
    task_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User,
) -> Task:
    """Link a global tag to a specific task.

    Args:
        db: Database session.
        task_id: UUID of the task.
        tag_id: UUID of the tag.
        current_user: Authenticated User making the request.

    Returns:
        The updated Task instance with tags loaded.
    """
    task = await get_or_404(db, task_id)
    await _assert_project_access(db, task, current_user)

    tag_repo = TagRepository(db)
    tag = await tag_repo.get_by_id(tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    return await task_repository.add_tag(db, task_id, tag)


async def detach_tag(
    db: AsyncSession,
    task_id: uuid.UUID,
    tag_id: uuid.UUID,
    current_user: User,
) -> Task:
    """Unlink a tag from a task.

    Args:
        db: Database session.
        task_id: UUID of the task.
        tag_id: UUID of the tag.
        current_user: Authenticated User.

    Returns:
        The updated Task instance with remaining tags.
    """
    task = await get_or_404(db, task_id)
    await _assert_project_access(db, task, current_user)

    tag_repo = TagRepository(db)
    tag = await tag_repo.get_by_id(tag_id)
    if tag is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    return await task_repository.remove_tag(db, task_id, tag)
