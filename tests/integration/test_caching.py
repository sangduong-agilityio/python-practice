"""
Integration tests for Redis Caching.

Ensure read operations hit the cache and write operations bust it.
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch
from tests.conftest import TEST_USER, auth_headers, create_user

@pytest.mark.asyncio
async def test_project_cache_flow(client: AsyncClient, mock_redis):
    """Check that project creation busts the list cache."""
    await create_user(client)
    headers = await auth_headers(client)
    
    # warm up the cache
    await client.get("/api/v1/projects", headers=headers)
    
    # trigger invalidation
    mock_redis.delete.reset_mock()
    await client.post("/api/v1/projects", json={"title": "Invalidator"}, headers=headers)
    assert mock_redis.delete.called

@pytest.mark.asyncio
async def test_tag_cache_flow(client: AsyncClient, mock_redis):
    """Check that tag creation busts the tag list cache."""
    await create_user(client)
    headers = await auth_headers(client)
    
    # query once to stash it
    await client.get("/api/v1/tags", headers=headers)
    
    # creating a new tag should delete the old cached response
    mock_redis.delete.reset_mock()
    await client.post("/api/v1/tags", json={"name": "CacheBuster", "color": "#112233"}, headers=headers)
    assert mock_redis.delete.called
