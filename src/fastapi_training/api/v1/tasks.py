from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ...schemas.task import TaskCreate, TaskResponse, TaskUpdate, TaskStatus
from ...services.task_service import (
    create_task,
    get_tasks_for_user,
    get_task_by_id,
    update_task,
    delete_task,
    filter_tasks_by_status,
    search_tasks_by_title,
)
from ..deps import get_current_user, get_db
from ...models.user import User

router = APIRouter(prefix="/tasks", tags=["Tasks"])


from .websocket_demo import notification_manager

@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task_route(
    task: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    new_task = await create_task(db, task, current_user.id)
    
    # Send a real-time notification to all connected clients
    await notification_manager.broadcast({
        "type": "new_task",
        "message": f"User {current_user.email} created a new task: {new_task.title}",
        "task_id": new_task.id
    })
    
    return new_task


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks = await get_tasks_for_user(db, current_user.id)
    return tasks


@router.get("/filter/status", response_model=List[TaskResponse])
async def filter_tasks_by_status_route(
    task_status: TaskStatus = Query(..., alias="status", description="Task status to filter by"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks = await filter_tasks_by_status(db, current_user.id, task_status)
    return tasks


@router.get("/search/title", response_model=List[TaskResponse])
async def search_tasks_by_title_route(
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tasks = await search_tasks_by_title(db, current_user.id, q)
    return tasks


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_route(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to access this task")
    return task


@router.put("/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
async def update_task_route(
    task_id: int,
    task_update: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to update this task")
    updated_task = await update_task(db, task, task_update)
    
    # Send a real-time notification about the update
    # We broadcast the specific message including title and newest status
    await notification_manager.broadcast({
        "type": "status_update",
        "message": f"User {current_user.email} updated task '{updated_task.title}' to: {updated_task.status}",
        "task_id": updated_task.id,
        "new_status": updated_task.status
    })
    
    return updated_task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_route(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    task = await get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this task")
    await delete_task(db, task_id)
