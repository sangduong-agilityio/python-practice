"""
Project business logic.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    InvalidFieldException,
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Handles project-related business operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    async def get_or_404(self, project_id: int) -> Project:
        """Fetch a project by ID or raise a ResourceNotFoundException if not found."""
        project = await self.repo.get_by_id(project_id)
        if project is None:
            raise ResourceNotFoundException("Project")
        return project

    def assert_owner(self, project: Project, user: User) -> None:
        """Verify that a user is the owner of a project."""
        if project.owner_id != user.id:
            raise PermissionDeniedException(
                "You do not have permission to access this resource")

    async def create(self, data: ProjectCreate, owner: User) -> Project:
        """Create a new project associated with the given owner."""
        project = Project(title=data.title,
                          description=data.description, owner_id=owner.id)
        return await self.repo.create(project)

    async def list_for_user(self, owner: User, skip: int = 0, limit: int = 20) -> list[Project]:
        """Retrieve a paginated list of projects owned by a user."""
        return await self.repo.get_by_owner(owner.id, skip=skip, limit=limit)

    async def update(self, project_id: int, data: ProjectUpdate, current_user: User) -> Project:
        """Update a project's details, provided the user is the owner."""
        project = await self.get_or_404(project_id)
        self.assert_owner(project, current_user)
        try:
            return await self.repo.update(project, data.model_dump(exclude_none=True))
        except ValueError as e:
            raise InvalidFieldException(
                str(e).replace("Cannot update field: ", "")) from e

    async def delete(self, project_id: int, current_user: User) -> None:
        """Delete a project permanently."""
        project = await self.get_or_404(project_id)
        self.assert_owner(project, current_user)
        await self.repo.delete(project)
