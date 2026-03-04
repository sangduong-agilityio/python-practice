from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from ..schemas.task import TaskCreate, TaskResponse, TaskUpdate
from ..services.task_service import create_task_service, get_tasks_for_user_service, get_task_by_id_service, update_task_service, delete_task_service
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


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id(
    task_id: int,
    current_user=Depends(get_current_user)
):
    """
    Get a specific task by its ID (only access own task).
    - 404 if task does not exist
    - 403 if task belongs to another user
    """
    task = get_task_by_id_service(task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this task"
        )

    return task


@router.put("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user=Depends(get_current_user)
):
    """
    Update a specific task by its ID (only update own task).
    - Proper authorization
    - Correct HTTP codes (200 OK)
    """
    task = get_task_by_id_service(task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update this task"
        )

    updated_task = update_task_service(task, task_update)
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user=Depends(get_current_user)
):
    """
    Delete a specific task by its ID (only delete own task).
    - Proper authorization
    - Correct HTTP codes (204 No Content)
    """
    task = get_task_by_id_service(task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    if task["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this task"
        )

    delete_task_service(task_id)
