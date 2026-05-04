"""
Project business logic.
"""

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete_pattern, cache_get, cache_set

from app.core.exceptions import (
    PermissionDeniedException,
    ResourceNotFoundException,
)
from app.models.project import Project
from app.models.user import User
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate

log = structlog.get_logger(__name__)
_CACHE_PREFIX = "projects:user"


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
        project = await self.repo.create(project)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:{owner.id}:*")
        return project

    async def list_for_user(self, owner: User, skip: int = 0, limit: int = 20) -> list[Project]:
        """Retrieve a paginated list of projects owned by a user."""
        cache_key = f"{_CACHE_PREFIX}:{owner.id}:skip={skip}:limit={limit}"
        cached = await cache_get(cache_key)
        if cached is not None:
            log.info("cache.hit", key=cache_key)
            return cached
        log.info("cache.miss", key=cache_key)
        projects = await self.repo.get_by_owner(owner.id, skip=skip, limit=limit)
        from app.schemas.project import ProjectResponse
        serialised = [ProjectResponse.model_validate(p).model_dump(mode="json") for p in projects]
        await cache_set(cache_key, serialised)
        return projects

    async def update(self, project_id: int, data: ProjectUpdate, current_user: User) -> Project:
        """Update a project's details, provided the user is the owner."""
        project = await self.get_or_404(project_id)
        self.assert_owner(project, current_user)
        updated = await self.repo.update(project, data.model_dump(exclude_unset=True))
        await cache_delete_pattern(f"{_CACHE_PREFIX}:{current_user.id}:*")
        return updated

    async def delete(self, project_id: int, current_user: User) -> None:
        """Delete a project permanently."""
        project = await self.get_or_404(project_id)
        self.assert_owner(project, current_user)
        await self.repo.delete(project)
        await cache_delete_pattern(f"{_CACHE_PREFIX}:{current_user.id}:*")
