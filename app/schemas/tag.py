"""
app/schemas/tag.py
------------------
Pydantic schemas for Tag-related API input/output.
"""

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str = Field(default="#3B82F6", pattern=r"^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    """Schema for POST /tags."""
    pass


class TagOut(TagBase):
    """Response schema for a tag."""
    id: int

    model_config = {"from_attributes": True}
