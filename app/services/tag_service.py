import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_delete, cache_get, cache_set

from app.core.exceptions import (
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from app.models.tag import Tag
from app.repositories.tag_repository import TagRepository
from app.schemas.tag import TagCreate

log = structlog.get_logger(__name__)
_TAGS_CACHE_KEY = "tags:all"


class TagService:
    """Business logic for tags."""

    def __init__(self, db: AsyncSession):
        self.repo = TagRepository(db)

    async def create(self, data: TagCreate) -> Tag:
        """Create a new global tag."""
        if await self.repo.get_by_name(data.name):
            raise ResourceAlreadyExistsException(f"Tag '{data.name}' already exists")

        tag = Tag(name=data.name, color=data.color)
        tag = await self.repo.create(tag)
        await cache_delete(_TAGS_CACHE_KEY)
        return tag

    async def list_all(self) -> list[Tag]:
        """Retrieve all tags."""
        cached = await cache_get(_TAGS_CACHE_KEY)
        if cached is not None:
            log.info("cache.hit", key=_TAGS_CACHE_KEY)
            return cached
        log.info("cache.miss", key=_TAGS_CACHE_KEY)
        tags = await self.repo.get_all()
        from app.schemas.tag import TagResponse
        serialised = [TagResponse.model_validate(t).model_dump(mode="json") for t in tags]
        await cache_set(_TAGS_CACHE_KEY, serialised)
        return tags

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
        await cache_delete(_TAGS_CACHE_KEY)
