"""
Integration tests for tags.

Check tag creation, listing, retrieval and making sure tag names are unique.
"""

import pytest
from httpx import AsyncClient
from tests.conftest import TEST_USER, auth_headers, create_user

async def _setup(client: AsyncClient) -> dict:
    await create_user(client)
    return await auth_headers(client)

@pytest.mark.asyncio
async def test_tag_creation_and_uniqueness(client: AsyncClient):
    """Ensure duplicate tag names are bounced."""
    headers = await _setup(client)
    
    # valid creation
    r = await client.post("/api/v1/tags", json={"name": "DevOps", "color": "#00FF00"}, headers=headers)
    assert r.status_code == 201
    assert r.json()["name"] == "DevOps"
    
    # duplicates should hit a 409 conflict
    r = await client.post("/api/v1/tags", json={"name": "DevOps", "color": "#FF0000"}, headers=headers)
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_tag_listing_and_retrieval(client: AsyncClient):
    """Check list and retrieve."""
    headers = await _setup(client)
    tag_name = "UniqueTag"
    
    # create it first
    r = await client.post("/api/v1/tags", json={"name": tag_name, "color": "#123456"}, headers=headers)
    tag_id = r.json()["id"]
    
    # pull down the global list
    r = await client.get("/api/v1/tags", headers=headers)
    assert r.status_code == 200
    assert any(t["name"] == tag_name for t in r.json())
    
    # ditch the tag
    r = await client.delete(f"/api/v1/tags/{tag_id}", headers=headers)
    assert r.status_code == 204
    
    # confirm it actually vanished
    r = await client.get(f"/api/v1/tags/{tag_id}", headers=headers)
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_tag_unauthenticated_access(client: AsyncClient):
    """Endpoints should be gated by auth."""
    # list
    r = await client.get("/api/v1/tags")
    assert r.status_code == 401
    
    # create
    r = await client.post("/api/v1/tags", json={"name": "NoAuth", "color": "#000000"})
    assert r.status_code == 401
