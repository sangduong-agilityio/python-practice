from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .user import User
    from .project import Project


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    title: str = Field(index=True)
    description: Optional[str] = Field(default=None, nullable=True)
    status: str = Field(default="pending")
    user_id: int = Field(foreign_key="users.id")
    project_id: Optional[int] = Field(default=None, foreign_key="projects.id", nullable=True)
    is_deleted: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Relationships
    owner: Optional["User"] = Relationship(
        back_populates="tasks",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    project: Optional["Project"] = Relationship(
        back_populates="tasks",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
