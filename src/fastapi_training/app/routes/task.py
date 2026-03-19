from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

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
from ..dependencies.db import get_db
from ..models.user import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task: TaskCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    new_task = await create_task_service(db, task, current_user.id)
    return new_task

@router.get("/", response_model=List[TaskResponse])
async def get_tasks(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    tasks = await get_tasks_for_user_service(db, current_user.id)
    return tasks

@router.get("/filter/status", response_model=List[TaskResponse])
async def filter_tasks_by_status(
    status: TaskStatus = Query(..., description="Task status to filter by"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tasks = await filter_tasks_by_status_service(db, current_user.id, status)
    return tasks

@router.get("/search/title", response_model=List[TaskResponse])
async def search_tasks_by_title(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    tasks = await search_tasks_by_title_service(db, current_user.id, q)
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_by_id(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = await get_task_by_id_service(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to access this task"
        )
    return task

@router.put("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = await get_task_by_id_service(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to update this task"
        )
    updated_task = await update_task_service(db, task, task_update)
    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    task = await get_task_by_id_service(db, task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to delete this task"
        )
    await delete_task_service(db, task_id)
