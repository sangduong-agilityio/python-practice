"""
Async Redis cache helpers.

Provides a thin wrapper around the async redis-py client so the rest of
the application never has to deal with raw Redis connections directly.
Cache keys are namespaced by resource type to avoid collisions and to
make bulk invalidation straightforward.
"""

import hashlib
import json
from typing import Any

import redis.asyncio as aioredis
import structlog

from app.core.config import settings

log = structlog.get_logger(__name__)

# Prefix used for all blacklisted access-token keys.
_BLACKLIST_PREFIX = "token_blacklist:"

# Module-level client reused across requests within the same process.
# The async client is thread-safe and connection-pool-backed by default.
_redis: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Return (or lazily create) the module-level async Redis client.

    Using a module-level singleton avoids the overhead of creating a new
    connection pool on every request while remaining safe in a single-process
    async server like Uvicorn.

    Returns:
        A connected async Redis client instance.
    """
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis


async def cache_get(key: str) -> Any | None:
    """Retrieve a JSON-serialised value from the cache.

    Args:
        key: The cache key to look up.

    Returns:
        The deserialised Python object, or None on a cache miss.
    """
    client = get_redis_client()
    raw = await client.get(key)
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(key: str, value: Any, ttl: int | None = None) -> None:
    """Store a JSON-serialisable value in the cache.

    Args:
        key: The cache key to write.
        value: Any JSON-serialisable Python object.
        ttl: Time-to-live in seconds. Defaults to CACHE_TTL_SECONDS from settings.
    """
    client = get_redis_client()
    ttl = ttl if ttl is not None else settings.CACHE_TTL_SECONDS
    await client.setex(key, ttl, json.dumps(value))


async def cache_delete(key: str) -> None:
    """Remove a single key from the cache.

    Args:
        key: The cache key to delete.
    """
    client = get_redis_client()
    await client.delete(key)


async def cache_delete_pattern(pattern: str) -> None:
    """Delete all keys matching a glob-style pattern.

    Used to invalidate entire namespaces on write operations, e.g. flushing
    all paginated project list variants when a project is created or deleted.

    Args:
        pattern: A glob pattern such as 'projects:user:<uuid>:*'.
    """
    client = get_redis_client()
    keys: list[str] = []
    # Avoid Redis KEYS (O(N) on the whole keyspace). SCAN is incremental and safer.
    async for key in client.scan_iter(match=pattern, count=500):
        keys.append(key)
        if len(keys) >= 500:
            await client.delete(*keys)
            keys.clear()

    if keys:
        await client.delete(*keys)
        log.info("cache_invalidated", pattern=pattern, keys_deleted=len(keys))
    else:
        log.debug("cache_invalidation_noop", pattern=pattern, reason="no_matching_keys")


async def blacklist_token(token: str, ttl_seconds: int) -> None:
    """Add an access token to the blacklist so it cannot be reused.

    The key expires automatically after ``ttl_seconds`` -- the remaining
    lifetime of the token -- so Redis never accumulates stale entries.

    Args:
        token: The raw JWT string to invalidate.
        ttl_seconds: Seconds until the token would have expired naturally.
                     Pass 0 to use a minimum of 1 second (avoids a SETEX error).
    """
    client = get_redis_client()
    # Never store raw JWTs in Redis keys (size + accidental leakage in tooling).
    token_digest = hashlib.sha256(token.encode()).hexdigest()
    key = f"{_BLACKLIST_PREFIX}{token_digest}"
    ttl = max(ttl_seconds, 1)
    await client.setex(key, ttl, "1")


async def is_token_blacklisted(token: str) -> bool:
    """Return True if the token has been added to the blacklist (i.e. logged out).

    Args:
        token: The raw JWT string to check.

    Returns:
        True if the token is blacklisted, False otherwise.
    """
    client = get_redis_client()
    token_digest = hashlib.sha256(token.encode()).hexdigest()
    key = f"{_BLACKLIST_PREFIX}{token_digest}"
    return await client.exists(key) == 1
