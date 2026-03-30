from fastapi import APIRouter, Depends, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.project import ProjectCreate, ProjectResponse
from ...schemas.task import TaskResponse
from ...services.project_service import (
    create_project,
    get_projects_for_user,
    assign_task_to_project,
)
from ..deps import get_current_user, get_db
from ...models.user import User

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project_route(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_project = await create_project(db, project, current_user.id)
    return new_project


@router.get("/", response_model=List[ProjectResponse])
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects = await get_projects_for_user(db, current_user.id)
    return projects


@router.post(
    "/{project_id}/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
)
async def assign_task_to_project_route(
    project_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await assign_task_to_project(db, project_id, task_id, current_user.id)
    return task
