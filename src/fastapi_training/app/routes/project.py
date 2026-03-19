from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.project import ProjectCreate, ProjectResponse 
from ..schemas.task import TaskResponse
from ..services.project_service import (
    create_project_service,
    get_projects_for_user_service,
    assign_task_to_project_service
)
from ..dependencies.auth import get_current_user
from ..dependencies.db import get_db
from ..models.user import User

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    new_project = await create_project_service(db, project, current_user.id)
    return new_project

@router.get("/", response_model=List[ProjectResponse])
async def get_projects(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    projects = await get_projects_for_user_service(db, current_user.id)
    return projects

@router.post("/{project_id}/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def assign_task_to_project(
    project_id: int,
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await assign_task_to_project_service(
        db, project_id, task_id, current_user.id)
    if "error" in result:
        raise HTTPException(
            status_code=result["code"],
            detail=result["error"]
        )
    return result["task"]
