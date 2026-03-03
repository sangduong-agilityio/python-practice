from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from ..schemas.task import TaskCreate, TaskResponse
from ..services.task_service import create_task_service, get_tasks_for_user_service
from ..dependencies.auth import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, current_user=Depends(get_current_user)):
    """
    Create a new task for the authenticated user.
    """
    new_task = create_task_service(task, current_user["id"])
    return new_task


@router.get("/", response_model=List[TaskResponse])
def get_tasks(current_user=Depends(get_current_user)):
    """
    Get all tasks for the authenticated user.
    """
    tasks = get_tasks_for_user_service(current_user["id"])
    return tasks
