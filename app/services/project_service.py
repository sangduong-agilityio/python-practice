"""
Project business logic.

assert_owner is a thin guard used by every mutating operation.
Pulling it into its own function means the check is in one place
and cannot be accidentally omitted in a new endpoint.
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.user import User
from app.repositories import project_repository
from app.schemas.project import ProjectCreate, ProjectUpdate


async def get_or_404(db: AsyncSession, project_id: uuid.UUID) -> Project:
    """Fetch a project by ID or raise a 404 Not Found error.

    Args:
        db: Database session.
        project_id: UUID of the project.

    Returns:
        The fetched Project instance.

    Raises:
        HTTPException 404: If the project does not exist.
    """
    project = await project_repository.get_by_id(db, project_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def assert_owner(project: Project, user: User) -> None:
    """Verify that a user is the owner of a project.

    Args:
        project: The target Project instance.
        user: The User instance claiming access.

    Raises:
        HTTPException 403: If the user is not the owner.
    """
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your project")


async def create(db: AsyncSession, data: ProjectCreate, owner: User) -> Project:
    """Create a new project associated with the given owner.

    Args:
        db: Database session.
        data: Validation schema for project creation.
        owner: The User instance who will own the project.

    Returns:
        The newly created Project.
    """
    project = Project(title=data.title, description=data.description, owner_id=owner.id)
    return await project_repository.create(db, project)


async def list_for_user(
    db: AsyncSession,
    owner: User,
    skip: int = 0,
    limit: int = 20,
) -> list[Project]:
    """Retrieve a paginated list of projects owned by a user.

    Args:
        db: Database session.
        owner: The User whose projects are to be listed.
        skip: Pagination offset.
        limit: Maximum results to return.

    Returns:
        List of matching Project instances.
    """
    return await project_repository.get_by_owner(db, owner.id, skip=skip, limit=limit)


async def update(
    db: AsyncSession,
    project_id: uuid.UUID,
    data: ProjectUpdate,
    current_user: User,
) -> Project:
    """Update a project's details, provided the user is the owner.

    Args:
        db: Database session.
        project_id: UUID of the project to update.
        data: ProjectUpdate schema containing changes.
        current_user: The authenticated User initiating the request.

    Returns:
        The updated Project instance.

    Raises:
        HTTPException 404: If the project doesn't exist.
        HTTPException 403: If the current user doesn't own the project.
    """
    project = await get_or_404(db, project_id)
    assert_owner(project, current_user)
    return await project_repository.update(db, project, data.model_dump(exclude_none=True))


async def delete(db: AsyncSession, project_id: uuid.UUID, current_user: User) -> None:
    """Delete a project permanently.

    Args:
        db: Database session.
        project_id: UUID of the project to remove.
        current_user: The authenticated User initiating the request.

    Raises:
        HTTPException 404: If the project doesn't exist.
        HTTPException 403: If the current user doesn't own the project.
    """
    project = await get_or_404(db, project_id)
    assert_owner(project, current_user)
    await project_repository.delete(db, project)
