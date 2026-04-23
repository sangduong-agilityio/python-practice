from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.schemas.tag import TagCreate


class TagService:
    """Logic nghiệp vụ cho Tag."""

    def __init__(self, db: AsyncSession):
        self.repo = TagRepository(db)

    async def create(self, data: TagCreate) -> Tag:
        """Create a new global tag."""
        if await self.repo.get_by_name(data.name):
            raise ResourceAlreadyExistsException(f"Tag '{data.name}' already exists")

        tag = Tag(name=data.name, color=data.color)
        return await self.repo.create(tag)

    async def list_all(self) -> list[Tag]:
        """Retrieve all tags."""
        return await self.repo.get_all()

    async def get_or_404(self, tag_id: int) -> Tag:
        """Retrieve a tag by ID or raise 404."""
        tag = await self.repo.get_by_id(tag_id)
        if not tag:
            raise ResourceNotFoundException(f"Tag with ID {tag_id}")
        return tag

    async def delete(self, tag_id: int) -> None:
        """Delete a tag by ID."""
        tag = await self.get_or_404(tag_id)
        await self.repo.delete(tag)
