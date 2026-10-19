"""
app/models/tag.py
-----------------
SQLAlchemy ORM models for `tags` and the `task_tags` pivot table.

Many-to-many relationship between Task and Tag:
  - One task can have many tags (e.g. "backend", "urgent")
  - One tag can be applied to many tasks
  - The `task_tags` table stores only the (task_id, tag_id) pairs — it's a pivot/junction table.
"""

from sqlalchemy import ForeignKey, String, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


# ---------------------------------------------------------------------------
# Pivot / Junction Table (no Python class needed — just a Table object)
# ---------------------------------------------------------------------------
# SQLAlchemy uses this table automatically when you access task.tags or tag.tasks.
# We don't need a full class because we never query TaskTag directly.
TaskTag = Table(
    "task_tags",
    Base.metadata,
    Column("task_id", ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Tag(Base):
    """
    A label that can be attached to tasks to categorize them.

    Columns:
        id    : Auto-incrementing primary key.
        name  : Unique tag name (e.g. "backend", "urgent").
        color : Hex color string for UI display (e.g. "#FF5733").
    """

    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    color: Mapped[str] = mapped_column(String(7), default="#3B82F6", nullable=False)

    # Back-reference through the pivot table — access all tasks with this tag
    tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]
        "Task", secondary="task_tags", back_populates="tags"
    )

    def __repr__(self) -> str:
        return f"<Tag id={self.id} name={self.name!r}>"
