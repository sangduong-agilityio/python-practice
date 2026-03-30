"""
CRUD operations for Project model.
Pure database operations — no business logic.
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from ..models.project import Project
from ..models.task import Task


async def create_project_db(
    db: AsyncSession, name: str, description: Optional[str], user_id: int
) -> Project:
    """Insert a new project record and return it."""
    new_project = Project(name=name, description=description, user_id=user_id)
    db.add(new_project)
    await db.commit()
    await db.refresh(new_project)
    return new_project


async def get_projects_for_user(db: AsyncSession, user_id: int) -> List[Project]:
    """Fetch all projects owned by a given user."""
    result = await db.execute(select(Project).where(Project.user_id == user_id))
    return list(result.scalars().all())


async def get_project_by_id(db: AsyncSession, project_id: int) -> Optional[Project]:
    """Fetch a single project by primary key."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalars().first()


async def get_task_for_project(
    db: AsyncSession, task_id: int
) -> Optional[Task]:
    """Fetch an active (non-deleted) task by primary key."""
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.is_deleted == False) 
    )
    return result.scalars().first()


async def assign_task_to_project_db(
    db: AsyncSession, task: Task, project_id: int
) -> Task:
    """Set the project_id on a task and persist."""
    task.project_id = project_id
    await db.commit()
    await db.refresh(task)
    return task
