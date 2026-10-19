"""
app/schemas/task.py
-------------------
Pydantic schemas for Task-related API input/output.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.task import TaskPriority, TaskStatus
from app.schemas.tag import TagOut


class TaskBase(BaseModel):
    """Fields shared between create and response schemas."""
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: datetime | None = None


class TaskCreate(TaskBase):
    """Schema for POST /projects/{id}/tasks — request body."""
    pass


class TaskUpdate(BaseModel):
    """Schema for PUT /tasks/{id} — all fields optional."""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    due_date: datetime | None = None


class TaskStatusUpdate(BaseModel):
    """Schema for PATCH /tasks/{id}/status — change status only."""
    status: TaskStatus

    @field_validator("status", mode="before")
    @classmethod
    def normalize_status(cls, value: object) -> object:
        """Accept any casing (e.g. "DONE", "Done") by lowercasing before enum validation."""
        if isinstance(value, str):
            return value.strip().lower()
        return value


class TaskAssignUpdate(BaseModel):
    """Schema for PATCH /tasks/{id}/assign — assign or unassign a user."""
    assignee_id: int | None = None  # None = unassign


class TaskOut(TaskBase):
    """Full task response schema including computed/relational fields."""
    id: int
    status: TaskStatus
    project_id: int
    assignee_id: int | None
    tags: list[TagOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
