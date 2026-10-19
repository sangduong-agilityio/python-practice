"""
app/repositories/tag_repository.py
------------------------------------
Database access layer for the Tag model.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


class TagRepository:
    """Encapsulates all SQL queries related to the Tag model."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, tag_id: int) -> Tag | None:
        """Fetch a tag by primary key."""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Tag | None:
        """Fetch a tag by its unique name."""
        result = await self.db.execute(select(Tag).where(Tag.name == name.lower()))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Tag]:
        """Fetch all tags, ordered alphabetically."""
        result = await self.db.execute(select(Tag).order_by(Tag.name))
        return list(result.scalars().all())

    async def create(self, name: str, color: str = "#3B82F6") -> Tag:
        """Insert a new tag row."""
        tag = Tag(name=name.lower(), color=color)
        self.db.add(tag)
        await self.db.flush()
        await self.db.refresh(tag)
        return tag
