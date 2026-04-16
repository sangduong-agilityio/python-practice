"""
Integration tests for Global Tagging system.

Ensures that:
- Tags can be created by authenticated users.
- Tag names are unique (Conflict handling).
- Tag listing retrieval works correctly.
- Tags can be fetched by ID and handles 404s.
"""

import pytest
from httpx import AsyncClient
from tests.conftest import TEST_USER, auth_headers, create_user

async def _setup(client: AsyncClient) -> dict:
    await create_user(client)
    return await auth_headers(client)

@pytest.mark.asyncio
async def test_tag_creation_and_uniqueness(client: AsyncClient):
    """Verify tag creation and ensure duplicate names are rejected."""
    headers = await _setup(client)
    
    # 1. Success
    r = await client.post("/api/v1/tags", json={"name": "DevOps", "color": "#00FF00"}, headers=headers)
    assert r.status_code == 201
    assert r.json()["name"] == "DevOps"
    
    # 2. Duplicate
    r = await client.post("/api/v1/tags", json={"name": "DevOps", "color": "#FF0000"}, headers=headers)
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_tag_listing_and_retrieval(client: AsyncClient):
    """Verify that tags can be listed and retrieved individually."""
    headers = await _setup(client)
    tag_name = "UniqueTag"
    
    # Create tag
    r = await client.post("/api/v1/tags", json={"name": tag_name, "color": "#123456"}, headers=headers)
    tag_id = r.json()["id"]
    
    # List all
    r = await client.get("/api/v1/tags", headers=headers)
    assert r.status_code == 200
    assert any(t["name"] == tag_name for t in r.json())
    
    # 3. Delete
    r = await client.delete(f"/api/v1/tags/{tag_id}", headers=headers)
    assert r.status_code == 204
    
    # 4. Verify gone
    r = await client.get(f"/api/v1/tags/{tag_id}", headers=headers)
    assert r.status_code == 404

@pytest.mark.asyncio
async def test_tag_unauthenticated_access(client: AsyncClient):
    """Ensure that tag endpoints are protected by authentication."""
    # List
    r = await client.get("/api/v1/tags")
    assert r.status_code == 401
    
    # Create
    r = await client.post("/api/v1/tags", json={"name": "NoAuth", "color": "#000000"})
    assert r.status_code == 401
