"""
app/repositories/project_repository.py
---------------------------------------
Database access layer for the Project model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    """Encapsulates all SQL queries related to the Project model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, project_id: int) -> Project | None:
        """Fetch a project by primary key."""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def list_by_owner(
        self, owner_id: int, skip: int = 0, limit: int = 20
    ) -> list[Project]:
        """
        Fetch a paginated list of projects belonging to a specific user.

        Args:
            owner_id : The user's ID.
            skip     : How many rows to skip (for pagination, e.g. page 2 = skip 20).
            limit    : Max rows to return.
        """
        result = await self.db.execute(
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())  # Newest first
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(self, title: str, owner_id: int, description: str | None = None) -> Project:
        """Insert a new project row."""
        project = Project(title=title, description=description, owner_id=owner_id)
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project, **kwargs) -> Project:
        """Update arbitrary fields on an existing Project."""
        for field, value in kwargs.items():
            setattr(project, field, value)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project) -> None:
        """Delete a project row (cascades to tasks)."""
        await self.db.delete(project)
        await self.db.flush()
