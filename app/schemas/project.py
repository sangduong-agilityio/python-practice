"""
app/schemas/project.py
----------------------
Pydantic schemas for Project-related API input/output.
"""

from datetime import datetime

from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    """Fields shared between create and response schemas."""
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None


class ProjectCreate(ProjectBase):
    """Schema for POST /projects — request body."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for PUT /projects/{id} — all fields optional."""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None


class ProjectOut(ProjectBase):
    """Response schema returned after creating / fetching a project."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
