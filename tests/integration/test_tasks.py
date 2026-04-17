"""
Integration tests for tasks.

Exercises task creation, fetching, updating, deletion, assignment, and tagging.
Crucially verifies cross-user data isolation.
"""

import pytest
from httpx import AsyncClient
from tests.conftest import TEST_USER, SECOND_USER, auth_headers, create_user

async def _setup_project(client: AsyncClient, user_payload: dict = TEST_USER) -> tuple[dict, int]:
    """Helper to spin up a user and project quickly."""
    await create_user(client, user_payload)
    headers = await auth_headers(client, user_payload)
    r = await client.post("/api/v1/projects", json={"title": "Main Project"}, headers=headers)
    return headers, r.json()["id"]

@pytest.mark.asyncio
async def test_task_crud_with_permissions(client: AsyncClient):
    """Check standard crud operations and ensure bob can't touch alice's tasks."""
    alice_headers, alice_project_id = await _setup_project(client, TEST_USER)
    
    # start by creating a task we can manipulate
    r = await client.post(f"/api/v1/projects/{alice_project_id}/tasks", json={"title": "Alice Task"}, headers=alice_headers)
    task_id = r.json()["id"]
    
    # spin up an attacker account
    await create_user(client, SECOND_USER)
    bob_headers = await auth_headers(client, SECOND_USER)
    
    # bob shouldn't be able to view, edit, or delete alice's task
    assert (await client.get(f"/api/v1/tasks/{task_id}", headers=bob_headers)).status_code == 403
    assert (await client.put(f"/api/v1/tasks/{task_id}", json={"title": "Hacked"}, headers=bob_headers)).status_code == 403
    assert (await client.delete(f"/api/v1/tasks/{task_id}", headers=bob_headers)).status_code == 403
    
    # but alice can delete her own stuff just fine
    assert (await client.delete(f"/api/v1/tasks/{task_id}", headers=alice_headers)).status_code == 204
    
    # verify it's actually wiped
    assert (await client.get(f"/api/v1/tasks/{task_id}", headers=alice_headers)).status_code == 404

@pytest.mark.asyncio
async def test_task_assignment_logic(client: AsyncClient):
    """Test task assignment endpoints and failures."""
    headers, project_id = await _setup_project(client)
    r = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "AssignMe"}, headers=headers)
    task_id = r.json()["id"]
    
    # assigning a task to a ghost user should explicitly 404
    r = await client.patch(f"/api/v1/tasks/{task_id}/assign", json={"assignee_id": 99999}, headers=headers)
    assert r.status_code == 404
    
    # assigning to oneself should succeed
    r_user = await client.get("/api/v1/users/me", headers=headers)
    my_id = r_user.json()["id"]
    r = await client.patch(f"/api/v1/tasks/{task_id}/assign", json={"assignee_id": my_id}, headers=headers)
    assert r.status_code == 200
    assert r.json()["assignee_id"] == my_id

@pytest.mark.asyncio
async def test_task_tagging_logic(client: AsyncClient):
    """Make sure tagging handles duplicates and missing entities cleanly."""
    headers, project_id = await _setup_project(client)
    r = await client.post(f"/api/v1/projects/{project_id}/tasks", json={"title": "Taggy"}, headers=headers)
    task_id = r.json()["id"]
    
    # provision a dummy tag
    r = await client.post("/api/v1/tags", json={"name": "Frontend", "color": "#0000FF"}, headers=headers)
    tag_id = r.json()["id"]
    
    # basic attachment
    r = await client.post(f"/api/v1/tasks/{task_id}/tags/{tag_id}", headers=headers)
    assert r.status_code == 200
    
    # attaching the exact same tag again shouldn't crash (idempotency)
    r = await client.post(f"/api/v1/tasks/{task_id}/tags/{tag_id}", headers=headers)
    assert r.status_code == 200
    
    # touching a ghost tag drops a 404
    assert (await client.post(f"/api/v1/tasks/{task_id}/tags/0", headers=headers)).status_code == 404
    
    # clean detachment
    assert (await client.delete(f"/api/v1/tasks/{task_id}/tags/{tag_id}", headers=headers)).status_code == 200
    
    # removing a tag that's already gone is fine
    assert (await client.delete(f"/api/v1/tasks/{task_id}/tags/{tag_id}", headers=headers)).status_code == 200

@pytest.mark.asyncio
async def test_task_listing_isolation(client: AsyncClient):
    """Ensure listing project tasks respects cross-user isolation."""
    alice_headers, alice_project_id = await _setup_project(client, TEST_USER)
    
    await create_user(client, SECOND_USER)
    bob_headers = await auth_headers(client, SECOND_USER)
    
    # bob fetching alice's sub-tasks should fail with perm denied
    r = await client.get(f"/api/v1/projects/{alice_project_id}/tasks", headers=bob_headers)
    assert r.status_code == 403
