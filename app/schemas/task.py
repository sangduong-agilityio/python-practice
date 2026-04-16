from datetime import datetime

from pydantic import BaseModel, Field

from app.models.task import TaskPriority, TaskStatus
from app.schemas.tag import TagResponse


class TaskBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None
    status: TaskStatus | None = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskAssignUpdate(BaseModel):
    # Passing null explicitly unassigns the task.
    assignee_id: int | None = None


class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    project_id: int
    assignee_id: int | None
    tags: list[TagResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
