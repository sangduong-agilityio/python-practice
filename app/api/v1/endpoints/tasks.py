import uuid

from fastapi import APIRouter, BackgroundTasks, Query, status

from app.core.dependencies import CurrentUser, DbSession
from app.models.task import TaskPriority, TaskStatus
from app.schemas.task import (
    TaskAssignUpdate,
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
)
from app.services import task_service

router = APIRouter(tags=["tasks"])


@router.post("/projects/{project_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    project_id: uuid.UUID, data: TaskCreate, current_user: CurrentUser, db: DbSession
) -> TaskResponse:
    task = await task_service.create(db, project_id, data, current_user)
    return task 


@router.get("/projects/{project_id}/tasks", response_model=list[TaskResponse])
async def list_tasks(
    project_id: uuid.UUID,
    current_user: CurrentUser,
    db: DbSession,
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    priority_filter: TaskPriority | None = Query(default=None, alias="priority"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[TaskResponse]:
    tasks = await task_service.list_for_project(
        db, project_id, current_user,
        status_filter=status_filter,
        priority_filter=priority_filter,
        skip=skip,
        limit=limit,
    )
    return tasks 


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> TaskResponse:
    task = await task_service.get_or_404(db, task_id)
    await task_service._assert_project_access(db, task, current_user)
    return task 


@router.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: uuid.UUID, data: TaskUpdate, current_user: CurrentUser, db: DbSession
) -> TaskResponse:
    task = await task_service.update(db, task_id, data, current_user)
    return task 


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> None:
    await task_service.delete(db, task_id, current_user)


@router.patch("/tasks/{task_id}/status", response_model=TaskResponse)
async def change_status(
    task_id: uuid.UUID, data: TaskStatusUpdate, current_user: CurrentUser, db: DbSession
) -> TaskResponse:
    task = await task_service.change_status(db, task_id, data, current_user)
    return task  


@router.patch("/tasks/{task_id}/assign", response_model=TaskResponse)
async def assign_task(
    task_id: uuid.UUID,
    data: TaskAssignUpdate,
    current_user: CurrentUser,
    db: DbSession,
    background_tasks: BackgroundTasks,
) -> TaskResponse:
    task = await task_service.assign(db, task_id, data, current_user, background_tasks)
    return task  


@router.post("/tasks/{task_id}/tags/{tag_id}", response_model=TaskResponse)
async def add_tag(task_id: uuid.UUID, tag_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> TaskResponse:
    task = await task_service.attach_tag(db, task_id, tag_id, current_user)
    return task  


@router.delete("/tasks/{task_id}/tags/{tag_id}", response_model=TaskResponse)
async def remove_tag(task_id: uuid.UUID, tag_id: uuid.UUID, current_user: CurrentUser, db: DbSession) -> TaskResponse:
    task = await task_service.detach_tag(db, task_id, tag_id, current_user)
    return task  
