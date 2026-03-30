"""
Project service — business logic layer.
All database operations are delegated to crud.project.
"""
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.project import Project
from ..models.task import Task
from ..schemas.project import ProjectCreate
from ..crud import project as project_crud


async def create_project(
    db: AsyncSession, project_data: ProjectCreate, user_id: int
) -> Project:
    """Create a new project owned by the given user."""
    return await project_crud.create_project_db(
        db,
        name=project_data.name,
        description=project_data.description,
        user_id=user_id,
    )


async def get_projects_for_user(db: AsyncSession, user_id: int) -> List[Project]:
    """Return all projects for a user."""
    return await project_crud.get_projects_for_user(db, user_id)


async def get_project_by_id(db: AsyncSession, project_id: int) -> Optional[Project]:
    """Return a single project by ID."""
    return await project_crud.get_project_by_id(db, project_id)


async def assign_task_to_project(
    db: AsyncSession, project_id: int, task_id: int, current_user_id: int
) -> Task:
    """Assign a task to a project, enforcing ownership checks."""
    project = await project_crud.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    if project.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to assign to this project",
        )

    task = await project_crud.get_task_for_project(db, task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    if task.user_id != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to assign this task",
        )

    return await project_crud.assign_task_to_project_db(db, task, project.id)
