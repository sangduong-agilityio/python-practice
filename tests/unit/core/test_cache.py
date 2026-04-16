import hashlib
from unittest.mock import AsyncMock, patch

import pytest

from app.core import cache as cache_module


@pytest.mark.asyncio
async def test_blacklist_token_hashes_key() -> None:
    mock_client = AsyncMock()
    token = "header.payload.signature"

    with patch.object(cache_module, "get_redis_client", return_value=mock_client):
        await cache_module.blacklist_token(token, ttl_seconds=10)

    token_digest = hashlib.sha256(token.encode()).hexdigest()
    expected_key = f"token_blacklist:{token_digest}"
    mock_client.setex.assert_awaited_once()
    called_key = mock_client.setex.await_args.args[0]
    assert called_key == expected_key
    assert token not in called_key


@pytest.mark.asyncio
async def test_cache_delete_pattern_uses_scan_iter_and_deletes() -> None:
    deleted: list[str] = []

    class FakeRedis:
        async def delete(self, *keys: str) -> None:
            deleted.extend(keys)

        async def scan_iter(self, *, match: str, count: int = 500):
            # Yield a couple keys to simulate invalidation.
            yield f"{match}-1"
            yield f"{match}-2"

    fake = FakeRedis()

    with patch.object(cache_module, "get_redis_client", return_value=fake):
        await cache_module.cache_delete_pattern("projects:user:1:*")

    assert deleted == ["projects:user:1:*-1", "projects:user:1:*-2"]

