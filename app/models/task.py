"""
Task model with status/priority enums and a many-to-many tag relationship.

The pivot table (task_tags) is defined as a plain Table rather than a
full model class because it has no extra columns -- it is a pure join table.
SQLAlchemy manages inserts/deletes into it automatically via the relationship.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String, Table, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class TaskStatus(str, enum.Enum):
    # Inheriting str means JSON serialization works without a custom encoder.
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


task_tags = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="taskstatus"),
        default=TaskStatus.TODO,
        nullable=False,
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="taskpriority"),
        default=TaskPriority.MEDIUM,
        nullable=False,
    )
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        # SET NULL keeps the task when the assigned user is deleted,
        # rather than deleting the task along with the user.
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    project: Mapped["Project"] = relationship("Project", back_populates="tasks")  # type: ignore[name-defined]
    assignee: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assignee_id],
    )
    tags: Mapped[list["Tag"]] = relationship(  # type: ignore[name-defined]
        "Tag",
        secondary=task_tags,
        back_populates="tasks",
    )

    def __repr__(self) -> str:
        return f"<Task {self.title!r} [{self.status}]>"
