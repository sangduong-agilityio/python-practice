from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceAlreadyExistsException
from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.schemas.tag import TagCreate


class TagService:
    """Logic nghiệp vụ cho Tag."""

    def __init__(self, db: AsyncSession):
        self.repo = TagRepository(db)

    async def create(self, data: TagCreate) -> Tag:
        """Create a new global tag.

        Args:
            data: Validation schema containing tag name and color.

        Returns:
            The newly created Tag instance.

        Raises:
            ResourceAlreadyExistsException: If a tag with the same name already exists.
        """
        if await self.repo.get_by_name(data.name):
            raise ResourceAlreadyExistsException(f"Tag '{data.name}' already exists")
        
        tag = Tag(name=data.name, color=data.color)
        return await self.repo.create(tag)

    async def list_all(self) -> list[Tag]:
        """Retrieve all available tags in the platform.

        Returns:
            List of all Tag instances.
        """
        return await self.repo.list_all()
