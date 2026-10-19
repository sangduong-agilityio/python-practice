"""
app/models/task.py
------------------
SQLAlchemy ORM model for the `tasks` table.

Uses Python `enum.Enum` for status and priority fields, which are stored
as VARCHAR in the database but validated as enums in Python.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class TaskStatus(str, enum.Enum):
    """
    Allowed values for a task's current state.
    Inheriting from `str` means the enum value serializes as a plain string
    (important for JSON responses and DB storage).
    """
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskPriority(str, enum.Enum):
    """Allowed values for a task's urgency level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    """
    Represents a single unit of work within a project.

    Columns:
        id          : Auto-incrementing primary key.
        title       : Short task name.
        description : Optional detailed description.
        status      : One of: todo, in_progress, done.
        priority    : One of: low, medium, high.
        due_date    : Optional deadline (stored with timezone).
        project_id  : FK to projects.id.
        assignee_id : FK to users.id (nullable — task can be unassigned).
        created_at  : Set on INSERT.
        updated_at  : Updated on every UPDATE.
    """

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Enum columns: SQLAlchemy stores the string value, e.g. "todo"
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="taskstatus"), default=TaskStatus.TODO, nullable=False
    )
    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority, name="taskpriority"), default=TaskPriority.MEDIUM, nullable=False
    )

    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project_id: Mapped[int] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # nullable=True because a task might not be assigned to anyone yet
    assignee_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")  # type: ignore[name-defined]
    assignee: Mapped["User | None"] = relationship(  # type: ignore[name-defined]
        "User", back_populates="assigned_tasks", foreign_keys=[assignee_id]
    )
    # Many-to-many with Tag via the TaskTag pivot table
    tags: Mapped[list["Tag"]] = relationship(  # type: ignore[name-defined]
        "Tag", secondary="task_tags", back_populates="tasks"
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title!r} status={self.status}>"
