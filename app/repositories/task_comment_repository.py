"""
app/repositories/task_comment_repository.py
--------------------------------------------
Database access layer for the TaskComment model.

Soft-deleted comments (`is_deleted = True`) are invisible to every read here:
the list, the count and `get_by_id` share the same visibility filter.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_comment import TaskComment

VISIBLE = TaskComment.is_deleted.is_(False)


class TaskCommentRepository:
    """Encapsulates all SQL queries related to the TaskComment model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, task_id: int, author_id: int, content: str) -> TaskComment:
        """Insert a new comment row."""
        comment = TaskComment(task_id=task_id, author_id=author_id, content=content)
        self.db.add(comment)
        await self.db.flush()
        await self.db.refresh(comment)
        return comment

    async def get_by_id(self, comment_id: int) -> TaskComment | None:
        """Fetch a visible (not soft-deleted) comment by primary key."""
        result = await self.db.execute(
            select(TaskComment).where(TaskComment.id == comment_id, VISIBLE)
        )
        return result.scalar_one_or_none()

    async def list_by_task(
        self, task_id: int, limit: int = 20, offset: int = 0
    ) -> list[TaskComment]:
        """
        Fetch visible comments for a task, oldest first.

        `id` is a tiebreaker so pagination is stable when timestamps collide.
        """
        result = await self.db.execute(
            select(TaskComment)
            .where(TaskComment.task_id == task_id, VISIBLE)
            .order_by(TaskComment.created_at.asc(), TaskComment.id.asc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_task(self, task_id: int) -> int:
        """Count visible comments for a task (the pagination `total`)."""
        result = await self.db.execute(
            select(func.count())
            .select_from(TaskComment)
            .where(TaskComment.task_id == task_id, VISIBLE)
        )
        return result.scalar_one()
