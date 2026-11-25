"""
app/models/task_comment.py
--------------------------
SQLAlchemy ORM model for the `task_comments` table.

Comments are soft-deleted via `is_deleted` so history is preserved; list
queries must always filter on `is_deleted = False`.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Text, false, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TaskComment(Base):
    """
    A comment left on a task by a user.

    Columns:
        id         : Auto-incrementing primary key.
        task_id    : FK to tasks.id (comments are removed with their task).
        author_id  : FK to users.id — who wrote the comment; set to NULL if the
                     user is deleted so the comment history is preserved.
        content    : The comment text.
        is_deleted : Soft-delete flag; True rows are hidden from listings.
        created_at : Set on INSERT.
        updated_at : Updated on every UPDATE.
    """

    __tablename__ = "task_comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
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

    # Serves the list query: filter by task + is_deleted, order by created_at.
    __table_args__ = (
        Index(
            "ix_task_comments_task_id_is_deleted_created_at",
            "task_id",
            "is_deleted",
            "created_at",
        ),
    )

    def __repr__(self) -> str:
        return f"<TaskComment id={self.id} task_id={self.task_id} author_id={self.author_id}>"
