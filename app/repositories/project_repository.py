"""
Project repository -- raw database operations only.

Pagination uses offset/limit. For very large datasets a cursor-based
approach would be better, but offset is simpler and fine for most apps.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


async def get_by_id(db: AsyncSession, project_id: uuid.UUID) -> Project | None:
    """Fetch a project by primary key, or ``None`` if it does not exist."""
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def get_by_owner(
    db: AsyncSession,
    owner_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
) -> list[Project]:
    """Return a paginated list of projects owned by the given user.

    Results are ordered newest-first so the freshest work surfaces at the top
    of list views without any client-side sorting.

    Args:
        owner_id: UUID of the owning user.
        skip: Number of rows to skip (zero-based offset).
        limit: Maximum number of rows to return.

    Returns:
        A (possibly empty) list of ``Project`` instances.
    """
    result = await db.execute(
        select(Project)
        .where(Project.owner_id == owner_id)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all())


async def create(db: AsyncSession, project: Project) -> Project:
    """Persist a new ``Project`` and return it with server-generated fields populated."""
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def update(db: AsyncSession, project: Project, data: dict) -> Project:
    """Apply a partial field update to an existing ``Project`` and commit.

    Args:
        project: The tracked ORM instance to modify.
        data: Mapping of field names to new values.

    Returns:
        The refreshed ``Project`` instance.
    """
    for field, value in data.items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return project


async def delete(db: AsyncSession, project: Project) -> None:
    """Delete a ``Project`` row and commit the transaction.

    The ``ondelete="CASCADE"`` constraints in the schema ensure that all child
    tasks are removed by the database engine before this commit returns.
    """
    await db.delete(project)
    await db.commit()
