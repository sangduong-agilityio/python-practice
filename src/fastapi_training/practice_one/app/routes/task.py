from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional

from ..schemas.task import TaskCreate, TaskResponse, TaskUpdate, TaskStatus
from ..services.task_service import (
    create_task_service,
    get_tasks_for_user_service,
    get_task_by_id_service,
    update_task_service,
    delete_task_service,
    filter_tasks_by_status_service,
    search_tasks_by_title_service
)
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


@router.get("/filter/status", response_model=List[TaskResponse])
def filter_tasks_by_status(
    status: TaskStatus = Query(..., description="Task status to filter by"),
    current_user=Depends(get_current_user)
):
    """
    Filter tasks by status for the authenticated user.
    """
    tasks = filter_tasks_by_status_service(current_user["id"], status)
    return tasks


@router.get("/search/title", response_model=List[TaskResponse])
def search_tasks_by_title(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user=Depends(get_current_user)
):
    """
    Search tasks by title for the authenticated user.
    """
    tasks = search_tasks_by_title_service(current_user["id"], q)
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
def get_task_by_id(
    task_id: int,
    current_user=Depends(get_current_user)
):
    """
    Get a specific task by its ID (only access own task).
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
    Update a specific task by its ID (only update own task) 
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
