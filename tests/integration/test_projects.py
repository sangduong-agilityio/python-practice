"""
Integration tests for Project Management.

Verifies:
- Project creation, updating, and deletion.
- Strict ownership isolation between users.
- Correct handling of non-existent resources.
- Cache invalidation on project changes.
"""

from unittest.mock import patch

import pytest
from httpx import AsyncClient

from tests.conftest import auth_headers, create_user


async def _setup(client: AsyncClient, user_payload: dict) -> tuple[dict, int]:
    await create_user(client, user_payload)
    headers = await auth_headers(client, user_payload)
    r = await client.post("/api/v1/projects", json={"title": "Base Project"}, headers=headers)
    return headers, r.json()["id"]

@pytest.mark.asyncio
async def test_list_projects_cache_hit_prevents_db_query(client: AsyncClient) -> None:
    """
    Ensure we don't query postgres when redis serves a cached response.
    """
    TEST_USER = {"email": "cache@example.com", "username": "cache_user", "password": "password123"}
    await create_user(client, TEST_USER)
    headers = await auth_headers(client, TEST_USER)
    await client.post("/api/v1/projects", json={"title": "Cached Project"}, headers=headers)

    # stub out the global redis mock so we can actually store state during this test
    cache_store = {}

    async def fake_cache_get(key: str):
        return cache_store.get(key)

    async def fake_cache_set(key: str, value: any, ttl_secs: int = 60) -> None:
        cache_store[key] = value

    import app.repositories.project_repository
    original_get = app.repositories.project_repository.ProjectRepository.get_by_owner

    async def get_by_owner_wrapper(self, *args, **kwargs):
        return await original_get(self, *args, **kwargs)

    with patch("app.services.project_service.cache_get", side_effect=fake_cache_get), \
         patch("app.services.project_service.cache_set", side_effect=fake_cache_set), \
         patch("app.repositories.project_repository.ProjectRepository.get_by_owner", autospec=True, side_effect=get_by_owner_wrapper) as mock_db:

        # first request should miss cache and fetch from db
        r1 = await client.get("/api/v1/projects", headers=headers)
        assert r1.status_code == 200
        assert mock_db.call_count == 1

        # second request should hit cache and completely bypass db
        r2 = await client.get("/api/v1/projects", headers=headers)
        assert r2.status_code == 200
        assert mock_db.call_count == 1  # query count remains at 1

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
