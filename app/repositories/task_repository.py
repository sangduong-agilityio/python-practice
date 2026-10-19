"""
app/repositories/task_repository.py
-------------------------------------
Database access layer for the Task model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.task import Task, TaskPriority, TaskStatus
from app.models.tag import Tag


class TaskRepository:
    """Encapsulates all SQL queries related to the Task model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, task_id: int) -> Task | None:
        """
        Fetch a task by primary key, eagerly loading its tags.

        selectinload avoids the N+1 query problem: instead of running
        one query per tag, it fetches all tags in a single IN() query.
        """
        result = await self.db.execute(
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.tags))
        )
        return result.scalar_one_or_none()

    async def list_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 20,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
    ) -> list[Task]:
        """
        Fetch tasks for a project, with optional filters and pagination.

        Args:
            project_id : Filter to this project.
            skip       : Offset for pagination.
            limit      : Max rows.
            status     : Optional status filter (e.g. "todo").
            priority   : Optional priority filter (e.g. "high").
        """
        query = (
            select(Task)
            .where(Task.project_id == project_id)
            .options(selectinload(Task.tags))
            .order_by(Task.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Only add WHERE clauses when a filter is provided
        if status:
            query = query.where(Task.status == status)
        if priority:
            query = query.where(Task.priority == priority)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(
        self,
        title: str,
        project_id: int,
        description: str | None = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_date=None,
    ) -> Task:
        """Insert a new task row."""
        task = Task(
            title=title,
            description=description,
            project_id=project_id,
            priority=priority,
            due_date=due_date,
        )
        self.db.add(task)
        await self.db.flush()
        # Fetch fresh task with eager-loaded tags to prevent async MissingGreenlet
        created_task = await self.get_by_id(task.id)
        return created_task or task

    async def update(self, task: Task, **kwargs) -> Task:
        """Update arbitrary fields on an existing Task."""
        for field, value in kwargs.items():
            setattr(task, field, value)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete(self, task: Task) -> None:
        """Delete a task row."""
        await self.db.delete(task)
        await self.db.flush()

    async def add_tag(self, task: Task, tag: Tag) -> Task:
        """Attach a tag to a task (many-to-many via task_tags pivot)."""
        if tag not in task.tags:
            task.tags.append(tag)
            await self.db.flush()
        return task

    async def add_tags(self, task: Task, tags: list[Tag]) -> Task:
        """
        Attach multiple tags to a task in a single flush.

        Re-fetches the task with selectinload(Task.tags) so the collection is
        guaranteed to be loaded (avoids MissingGreenlet), skips tags that are
        already attached, and de-duplicates the input.
        """
        loaded_task = await self.get_by_id(task.id)
        if loaded_task is None:
            return task

        existing_ids = {t.id for t in loaded_task.tags}
        added = False
        for tag in tags:
            if tag.id not in existing_ids:
                loaded_task.tags.append(tag)
                existing_ids.add(tag.id)
                added = True

        if added:
            await self.db.flush()
        return loaded_task

    async def remove_tag(self, task: Task, tag: Tag) -> Task:
        """Detach a tag from a task."""
        if tag in task.tags:
            task.tags.remove(tag)
            await self.db.flush()
        return task
