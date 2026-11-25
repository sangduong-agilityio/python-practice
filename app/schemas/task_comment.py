"""
app/schemas/task_comment.py
---------------------------
Pydantic schemas for Task Comment API input/output.
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class TaskCommentCreate(BaseModel):
    """Schema for POST /tasks/{id}/comments — request body."""

    content: str = Field(min_length=1, max_length=5000)

    @field_validator("content", mode="before")
    @classmethod
    def strip_content(cls, value: object) -> object:
        """Trim whitespace so blank/whitespace-only comments fail min_length (422)."""
        if isinstance(value, str):
            return value.strip()
        return value


class TaskCommentResponse(BaseModel):
    """A single comment in API responses."""

    id: int
    task_id: int
    author_id: int | None
    content: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskCommentList(BaseModel):
    """Paginated list of comments."""

    items: list[TaskCommentResponse]
    total: int
    limit: int
    offset: int
