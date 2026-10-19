"""
app/services/tag_service.py
-----------------------------
Business logic for tag creation and listing.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.schemas.tag import TagCreate


class TagService:
    """Handles tag-related business operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = TagRepository(db)

    async def create(self, data: TagCreate) -> Tag:
        """
        Create a new tag, ensuring the name is unique.

        Args:
            data: Validated tag data.

        Returns:
            Newly created Tag object.

        Raises:
            HTTPException 400: If a tag with that name already exists.
        """
        existing = await self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Tag '{data.name}' already exists",
            )
        return await self.repo.create(name=data.name, color=data.color)

    async def list_all(self) -> list[Tag]:
        """Return all tags."""
        return await self.repo.list_all()
