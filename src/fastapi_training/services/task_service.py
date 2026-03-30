"""
Task service — business logic layer.
All database operations are delegated to crud.task.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.task import Task
from ..schemas.task import TaskCreate, TaskUpdate
from ..crud import task as task_crud


async def create_task(db: AsyncSession, task_data: TaskCreate, user_id: int) -> Task:
    """Create a new task for the given user."""
    return await task_crud.create_task_db(
        db,
        title=task_data.title,
        description=task_data.description,
        status=task_data.status,
        user_id=user_id,
        project_id=task_data.project_id,
    )


async def get_tasks_for_user(db: AsyncSession, user_id: int) -> List[Task]:
    """Return all active tasks for a user."""
    return await task_crud.get_tasks_for_user(db, user_id)


async def get_task_by_id(db: AsyncSession, task_id: int) -> Optional[Task]:
    """Return a single active task by ID."""
    return await task_crud.get_task_by_id(db, task_id)


async def update_task(db: AsyncSession, task: Task, update_data: TaskUpdate) -> Task:
    """Apply partial updates to a task."""
    update_dict = update_data.model_dump(exclude_unset=True)
    return await task_crud.update_task_db(db, task, update_dict)


async def delete_task(db: AsyncSession, task_id: int) -> bool:
    """Soft-delete a task by ID. Returns False if not found."""
    task = await task_crud.get_task_by_id(db, task_id)
    if not task:
        return False
    return await task_crud.soft_delete_task(db, task)


async def filter_tasks_by_status(
    db: AsyncSession, user_id: int, task_status: str
) -> List[Task]:
    """Return active tasks for a user matching the given status."""
    return await task_crud.filter_tasks_by_status(db, user_id, task_status)


async def search_tasks_by_title(
    db: AsyncSession, user_id: int, search_query: str
) -> List[Task]:
    """Return active tasks for a user whose title matches the query."""
    return await task_crud.search_tasks_by_title(db, user_id, search_query)
