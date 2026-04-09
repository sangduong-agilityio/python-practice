"""
Task repository.

selectinload is used to eagerly load the tags relationship in a second
SELECT rather than a JOIN. For a many-to-many this avoids row duplication
in the result set when a task has multiple tags.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import Tag
from app.models.task import Task, TaskPriority, TaskStatus


def _with_tags(stmt):
    # Centralise the eager-load option so every query in this file
    # returns tasks that already have tags loaded -- no lazy loads later.
    """Attach a ``selectinload`` option for ``Task.tags`` to a SELECT statement.

    Using a second SELECT (selectinload) rather than a JOIN avoids row
    duplication when a task has multiple tags.
    """
    return stmt.options(selectinload(Task.tags))


async def get_by_id(db: AsyncSession, task_id: uuid.UUID) -> Task | None:
    """Fetch a task by primary key with tags eagerly loaded, or ``None``."""
    result = await db.execute(_with_tags(select(Task).where(Task.id == task_id)))
    return result.scalar_one_or_none()


async def get_by_project(
    db: AsyncSession,
    project_id: uuid.UUID,
    status: TaskStatus | None = None,
    priority: TaskPriority | None = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Task]:
    """Return a filtered, paginated list of tasks for a project.

    All parameters except ``db`` and ``project_id`` are optional. Omitting
    ``status`` or ``priority`` returns tasks regardless of those fields.

    Args:
        project_id: Scope the query to this project.
        status: If provided, only return tasks in this status.
        priority: If provided, only return tasks at this priority level.
        skip: Zero-based row offset for pagination.
        limit: Maximum number of tasks to return (server-side cap: 200).

    Returns:
        A (possibly empty) list of ``Task`` instances with tags loaded.
    """
    stmt = select(Task).where(Task.project_id == project_id)

    if status is not None:
        stmt = stmt.where(Task.status == status)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)

    stmt = _with_tags(stmt).order_by(Task.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def create(db: AsyncSession, task: Task) -> Task:
    """Persist a new ``Task``, commit, and re-fetch with tags eagerly loaded.

    The extra SELECT after commit is intentional: a fresh ``db.refresh`` alone
    would not populate the ``tags`` relationship, so we re-run the query with
    ``_with_tags`` to guarantee a consistent object is returned.
    """
    db.add(task)
    await db.commit()
    await db.refresh(task)
    # Reload with tags so the returned object is consistent with other queries.
    result = await db.execute(_with_tags(select(Task).where(Task.id == task.id)))
    return result.scalar_one()


async def update(db: AsyncSession, task: Task, data: dict) -> Task:
    """Apply a partial field update to an existing ``Task`` and commit.

    Args:
        task: The tracked ORM instance to mutate.
        data: Mapping of attribute names to new values. Callers that want to
              clear nullable fields should pass ``exclude_unset=True`` (not
              ``exclude_none=True``) when building this dict.

    Returns:
        The refreshed ``Task`` instance.
    """
    for field, value in data.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete(db: AsyncSession, task: Task) -> None:
    """Delete a ``Task`` row and commit. Child rows (task_tags) are removed by DB cascade."""
    await db.delete(task)
    await db.commit()


async def add_tag(db: AsyncSession, task_id: uuid.UUID, tag: Tag) -> Task:
    """Associate a ``Tag`` with a task, skipping the operation if already linked.

    The task is re-fetched before mutation to avoid operating on a stale
    in-memory collection that might be missing tags added by concurrent requests.

    Args:
        task_id: UUID of the task to tag.
        tag: The ``Tag`` ORM instance to attach.

    Returns:
        The updated ``Task`` with the full tags collection eagerly loaded.
    """
    # Re-fetch with tags loaded to avoid operating on a stale collection.
    result = await db.execute(_with_tags(select(Task).where(Task.id == task_id)))
    task = result.scalar_one()
    if tag not in task.tags:
        task.tags.append(tag)
        await db.commit()
    return task


async def remove_tag(db: AsyncSession, task_id: uuid.UUID, tag: Tag) -> Task:
    """Detach a ``Tag`` from a task by filtering it out of the relationship list.

    If the tag is not currently linked, the operation is a no-op (no error).

    Args:
        task_id: UUID of the task to modify.
        tag: The ``Tag`` ORM instance to remove.

    Returns:
        The updated ``Task`` with the remaining tags eagerly loaded.
    """
    result = await db.execute(_with_tags(select(Task).where(Task.id == task_id)))
    task = result.scalar_one()
    task.tags = [t for t in task.tags if t.id != tag.id]
    await db.commit()
    return task
