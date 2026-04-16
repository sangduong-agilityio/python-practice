"""
Tag endpoints -- create, list, and manage tags on tasks.

GET /tags is cached in Redis because the tag list is a small, shared,
read-heavy resource that changes infrequently. The cache is invalidated
whenever a new tag is created.
"""

from fastapi import APIRouter, status

from app.core.cache import cache_delete, cache_get, cache_set
from app.core.dependencies import CurrentUser, DbSession
from app.schemas.tag import TagCreate, TagResponse
from app.services.tag_service import TagService
import structlog

router = APIRouter(prefix="/tags", tags=["tags"])
log = structlog.get_logger(__name__)

_TAGS_CACHE_KEY = "tags:all"

@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    data: TagCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> TagResponse:
    """Create a new global tag.

    Invalidates the cached tag list so the next GET /tags returns fresh data.

    Args:
        data: Tag creation payload (name and optional color).
        current_user: Authenticated user performing the action.
        db: Injected async database session.

    Returns:
        The created tag.
    """
    service = TagService(db)
    tag = await service.create(data)
    await cache_delete(_TAGS_CACHE_KEY)
    return tag


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: CurrentUser,
    db: DbSession,
) -> list[TagResponse]:
    """List all available tags.

    The result is cached in Redis because the tag list is global, small,
    and changes rarely relative to how often it is read.

    Args:
        current_user: Authenticated user making the request.
        db: Injected async database session.

    Returns:
        A list of all tags.
    """
    cached = await cache_get(_TAGS_CACHE_KEY)
    if cached is not None:
        log.info("cache.hit", key=_TAGS_CACHE_KEY)
        return cached

    log.info("cache.miss", key=_TAGS_CACHE_KEY)
    service = TagService(db)
    tags = await service.list_all()
    serialised = [TagResponse.model_validate(t).model_dump(mode="json") for t in tags]
    await cache_set(_TAGS_CACHE_KEY, serialised)
    return tags


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> TagResponse:
    """Retrieve a specific tag by its ID."""
    service = TagService(db)
    return await service.get_or_404(tag_id)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: int,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a global tag. Invalidates the tag cache."""
    service = TagService(db)
    await service.delete(tag_id)
    await cache_delete(_TAGS_CACHE_KEY)
