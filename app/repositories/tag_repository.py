"""
Tag repository -- raw database operations only.

Tags are global resources with no owner scoping, so queries here never
filter by user. Business-rule enforcement (duplicate name, etc.) lives
in the service layer.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


class TagRepository:
    """Raw database operations for tags."""
    
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tag_id: uuid.UUID) -> Tag | None:
        """Fetch a single tag by primary key, or ``None`` if it does not exist."""
        result = await self.db.execute(select(Tag).where(Tag.id == tag_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Tag | None:
        """Fetch a tag by its unique name (case-sensitive), or ``None`` on miss."""
        result = await self.db.execute(select(Tag).where(Tag.name == name))
        return result.scalar_one_or_none()

    async def get_all(self) -> list[Tag]:
        """Return every tag in the system, sorted alphabetically by name."""
        result = await self.db.execute(select(Tag).order_by(Tag.name))
        return list(result.scalars().all())

    async def create(self, tag: Tag) -> Tag:
        """Persist a new ``Tag`` instance and return the database-populated object."""
        self.db.add(tag)
        await self.db.commit()
        await self.db.refresh(tag)
        return tag
