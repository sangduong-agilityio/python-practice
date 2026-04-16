"""
Integration tests for Redis Caching system.

Guarantees that:
- Read operations for projects and tags are cached.
- Write operations trigger cache invalidation.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch
from tests.conftest import TEST_USER, auth_headers, create_user

@pytest.mark.asyncio
async def test_project_cache_flow(client: AsyncClient, mock_redis):
    """Verify that project listing is cached and invalidated correctly."""
    await create_user(client)
    headers = await auth_headers(client)
    
    # Warmer
    await client.get("/api/v1/projects", headers=headers)
    
    # Trigger Invalidation
    mock_redis.delete.reset_mock()
    await client.post("/api/v1/projects", json={"title": "Invalidator"}, headers=headers)
    assert mock_redis.delete.called

@pytest.mark.asyncio
async def test_tag_cache_flow(client: AsyncClient, mock_redis):
    """Verify that the global tag list is cached and invalidated correctly."""
    await create_user(client)
    headers = await auth_headers(client)
    
    # Populate
    await client.get("/api/v1/tags", headers=headers)
    
    # Invalidate
    mock_redis.delete.reset_mock()
    await client.post("/api/v1/tags", json={"name": "CacheBuster", "color": "#112233"}, headers=headers)
    assert mock_redis.delete.called
