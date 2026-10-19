"""
app/services/project_service.py
---------------------------------
Business logic for project CRUD operations.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Handles all project-related business operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = ProjectRepository(db)

    async def create(self, data: ProjectCreate, owner: User) -> Project:
        """
        Create a new project owned by the current user.

        Args:
            data  : Validated project data from request body.
            owner : The authenticated user creating the project.

        Returns:
            Newly created Project ORM object.
        """
        return await self.repo.create(
            title=data.title,
            description=data.description,
            owner_id=owner.id,
        )

    async def list_for_user(
        self, owner: User, skip: int = 0, limit: int = 20
    ) -> list[Project]:
        """Return a paginated list of projects belonging to `owner`."""
        return await self.repo.list_by_owner(owner.id, skip=skip, limit=limit)

    async def get_or_404(self, project_id: int) -> Project:
        """
        Fetch a project by ID, raising 404 if it doesn't exist.

        Args:
            project_id: The project's primary key.

        Returns:
            Project ORM object.

        Raises:
            HTTPException 404: If no project with that ID exists.
        """
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found",
            )
        return project

    def _check_owner(self, project: Project, user: User) -> None:
        """
        Verify that `user` owns `project`.

        Args:
            project : The project to check.
            user    : The authenticated user.

        Raises:
            HTTPException 403: If user is NOT the owner.
        """
        if project.owner_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to modify this project",
            )

    async def update(
        self, project_id: int, data: ProjectUpdate, current_user: User
    ) -> Project:
        """Fetch project, verify ownership, then apply updates."""
        project = await self.get_or_404(project_id)
        self._check_owner(project, current_user)

        updates = data.model_dump(exclude_none=True)  # Only changed fields
        if not updates:
            return project

        return await self.repo.update(project, **updates)

    async def delete(self, project_id: int, current_user: User) -> None:
        """Fetch project, verify ownership, then delete it."""
        project = await self.get_or_404(project_id)
        self._check_owner(project, current_user)
        await self.repo.delete(project)
