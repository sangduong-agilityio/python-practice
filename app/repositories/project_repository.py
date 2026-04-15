"""
Project repository -- raw database operations only.

Pagination uses offset/limit. For very large datasets a cursor-based
approach would be better, but offset is simpler and fine for most apps.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import UpdatableFields
from app.core.validation import validate_updatable_field
from app.models.project import Project


class ProjectRepository:
    """Raw database operations for projects."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: int) -> Project | None:
        """Fetch a project by primary key, or ``None`` if it does not exist."""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_by_owner(self, owner_id: int, skip: int = 0, limit: int = 20) -> list[Project]:
        """Return a paginated list of projects owned by the given user."""
        result = await self.db.execute(
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, project: Project) -> Project:
        """Persist a new ``Project`` and return it with server-generated fields populated."""
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project, data: dict) -> Project:
        """Apply a partial field update to an existing ``Project`` and commit.

        Only whitelisted fields (name, description) can be updated.
        System fields (id, owner_id, created_at) cannot be changed.

        Args:
            project: The project instance to update.
            data: Dictionary of fields to update.

        Returns:
            The updated project instance.

        Raises:
            InvalidFieldException: If attempting to update a non-whitelisted field.
        """
        for field, value in data.items():
            validate_updatable_field(field, UpdatableFields.PROJECT, "project")
