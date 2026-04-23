from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


class TagRepository:
    """Raw database operations for tags."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tag_id: int) -> Tag | None:
        """Fetch a single tag by primary key."""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Tag | None:
        """Fetch a tag by its unique name."""
        result = await self.db.execute(select(Tag).where(Tag.name == name))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Tag]:
        """Return every tag in the system."""
        result = await self.db.execute(select(Tag).order_by(Tag.name))
        return list(result.scalars().all())

    async def create(self, tag: Tag) -> Tag:
        """Persist a new Tag instance."""
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag

    async def delete(self, tag: Tag) -> None:
        """Delete a tag instance."""
        await self.db.delete(tag)
        await self.db.commit()
