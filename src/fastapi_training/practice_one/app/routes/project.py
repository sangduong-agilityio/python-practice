from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from ..schemas.project import ProjectCreate, ProjectResponse 
from ..schemas.task import TaskResponse
from ..services.project_service import (
    create_project_service,
    get_projects_for_user_service,
    assign_task_to_project_service
)
from ..dependencies.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    current_user=Depends(get_current_user)
):
    """
    Create a new project for the authenticated user.
    """
    new_project = create_project_service(project, current_user["id"])
    return new_project


@router.get("/", response_model=List[ProjectResponse])
def get_projects(current_user=Depends(get_current_user)):
    """
    Get all projects for the authenticated user.
    """
    projects = get_projects_for_user_service(current_user["id"])
    return projects


@router.post("/{project_id}/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def assign_task_to_project(
    project_id: int,
    task_id: int,
    current_user=Depends(get_current_user)
):
    """
    Assign a task to a project.

    Acceptance Criteria:
    - Only assign own task (task must belong to current user)
    - Proper validation (task & project must exist)
    - Authorization enforced (project must belong to current user)
    """
    result = assign_task_to_project_service(
        project_id, task_id, current_user["id"])

    if "error" in result:
        raise HTTPException(
            status_code=result["code"],
            detail=result["error"]
        )

    return result["task"]
