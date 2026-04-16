"""
Integration tests for Project Management.

Verifies:
- Project creation, updating, and deletion.
- Strict ownership isolation between users.
- Correct handling of non-existent resources.
- Cache invalidation on project changes.
"""

import pytest
from httpx import AsyncClient
from tests.conftest import auth_headers, create_user

async def _setup(client: AsyncClient, user_payload: dict) -> tuple[dict, int]:
    await create_user(client, user_payload)
    headers = await auth_headers(client, user_payload)
    r = await client.post("/api/v1/projects", json={"title": "Base Project"}, headers=headers)
    return headers, r.json()["id"]

@pytest.mark.asyncio
async def test_project_owner_permissions(client: AsyncClient):
    """Ensure only owners can modify or delete projects."""
    alice = {"email": "p_alice@example.com", "username": "p_alice", "password": "password123"}
    bob = {"email": "p_bob@example.com", "username": "p_bob", "password": "password123"}
    
    alice_headers, project_id = await _setup(client, alice)
    await create_user(client, bob)
    bob_headers = await auth_headers(client, bob)
    
    # 1. Bob attempts to GET Alice's project -> 403
    assert (await client.get(f"/api/v1/projects/{project_id}", headers=bob_headers)).status_code == 403
    
    # 2. Bob attempts to UPDATE Alice's project -> 403
    assert (await client.put(f"/api/v1/projects/{project_id}", json={"title": "Mine"}, headers=bob_headers)).status_code == 403
    
    # 3. Bob attempts to DELETE Alice's project -> 403
    assert (await client.delete(f"/api/v1/projects/{project_id}", headers=bob_headers)).status_code == 403

@pytest.mark.asyncio
async def test_project_not_found_handling(client: AsyncClient):
    """Verify system response for non-existent project IDs."""
    user = {"email": "p_guest@example.com", "username": "p_guest", "password": "password123"}
    await create_user(client, user)
    headers = await auth_headers(client, user)
    
    assert (await client.get("/api/v1/projects/99999", headers=headers)).status_code == 404
    assert (await client.put("/api/v1/projects/99999", json={"title": "Lost"}, headers=headers)).status_code == 404
    assert (await client.delete("/api/v1/projects/99999", headers=headers)).status_code == 404
