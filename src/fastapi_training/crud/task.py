"""
CRUD operations for Task model.
Pure database operations — no business logic.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.task import Task


async def create_task_db(
    db: AsyncSession,
    title: str,
    description: Optional[str],
    status: str,
    user_id: int,
    project_id: Optional[int],
) -> Task:
    """Insert a new task record and return it."""
    new_task = Task(
        title=title,
        description=description,
        status=status,
        user_id=user_id,
        project_id=project_id,
        is_deleted=False,
    )
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    return new_task


async def get_tasks_for_user(db: AsyncSession, user_id: int) -> List[Task]:
    """Fetch all active tasks owned by a user."""
    result = await db.execute(
        select(Task).where(Task.user_id == user_id, Task.is_deleted == False)
    )
    return list(result.scalars().all())


async def get_task_by_id(db: AsyncSession, task_id: int) -> Optional[Task]:
    """Fetch a single active task by primary key."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.is_deleted == False)
    )
    return result.scalars().first()


async def update_task_db(db: AsyncSession, task: Task, update_dict: dict) -> Task:
    """Apply a dict of field updates to an existing task and persist."""
    for key, value in update_dict.items():
        setattr(task, key, value)
    await db.commit()
    await db.refresh(task)
    return task


async def soft_delete_task(db: AsyncSession, task: Task) -> bool:
    """Mark a task as deleted (soft delete) and persist."""
    task.is_deleted = True
    await db.commit()
    return True


async def filter_tasks_by_status(
    db: AsyncSession, user_id: int, task_status: str
) -> List[Task]:
    """Fetch active tasks for a user filtered by status."""
    result = await db.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.is_deleted == False,
            Task.status == task_status,
        )
    )
    return list(result.scalars().all())


async def search_tasks_by_title(
    db: AsyncSession, user_id: int, search_query: str
) -> List[Task]:
    """Fetch active tasks for a user whose title matches the search query (case-insensitive)."""
    result = await db.execute(
        select(Task).where(
            Task.user_id == user_id,
            Task.is_deleted == False,
            Task.title.ilike(f"%{search_query}%"),
        )
    )
    return list(result.scalars().all())
