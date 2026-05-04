"""
Task repository.

selectinload is used to eagerly load the tags relationship in a second
SELECT rather than a JOIN. For a many-to-many this avoids row duplication
in the result set when a task has multiple tags.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import UpdatableFields
from app.core.validation import validate_updatable_field
from app.models.tag import Tag
from app.models.task import Task, TaskPriority, TaskStatus


def _with_tags(stmt):
    """Attach a ``selectinload`` option for ``Task.tags`` to a SELECT statement."""
    return stmt.options(selectinload(Task.tags))


class TaskRepository:
    """Raw database operations for tasks."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, task_id: int) -> Task | None:
        """Fetch a task by primary key with tags eagerly loaded, or ``None``."""
        result = await self.db.execute(_with_tags(select(Task).where(Task.id == task_id)))
        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: int,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Task]:
        """Return a filtered, paginated list of tasks for a project."""
        stmt = select(Task).where(Task.project_id == project_id)

        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)

        stmt = _with_tags(stmt).order_by(
            Task.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, task: Task) -> Task:
        """Persist a new ``Task``, flush, and re-fetch with tags eagerly loaded."""
        self.db.add(task)
        await self.db.flush()
        result = await self.db.execute(_with_tags(select(Task).where(Task.id == task.id)))
        return result.scalar_one()

    async def update(self, task: Task, data: dict) -> Task:
        """Apply a partial field update to an existing ``Task`` and commit.

        Only whitelisted fields (title, description, priority, status, due_date, assignee_id) can be updated.
        System fields (id, project_id, created_at) cannot be changed.

        Args:
            task: The task instance to update.
            data: Dictionary of fields to update.

        Returns:
            The updated task instance.

        Raises:
            InvalidFieldException: If attempting to update a non-whitelisted field.
        """
        for field, value in data.items():
            validate_updatable_field(field, UpdatableFields.TASK, "task")
            setattr(task, field, value)
        await self.db.flush()
        result = await self.db.execute(_with_tags(select(Task).where(Task.id == task.id)))
        return result.scalar_one()

    async def delete(self, task: Task) -> None:
        """Delete a ``Task`` row and commit. Child rows (task_tags) are removed by DB cascade."""
        await self.db.delete(task)
        await self.db.flush()

    async def add_tag(self, task_id: int, tag: Tag) -> Task:
        """Associate a ``Tag`` with a task, skipping the operation if already linked."""
        result = await self.db.execute(_with_tags(select(Task).where(Task.id == task_id)))
        task = result.scalar_one()
        if tag not in task.tags:
            task.tags.append(tag)
            await self.db.flush()
        return task

    async def remove_tag(self, task_id: int, tag: Tag) -> Task:
        """Detach a ``Tag`` from a task by filtering it out of the relationship list."""
        result = await self.db.execute(_with_tags(select(Task).where(Task.id == task_id)))
        task = result.scalar_one()
        task.tags = [t for t in task.tags if t.id != tag.id]
        await self.db.flush()
        return task
