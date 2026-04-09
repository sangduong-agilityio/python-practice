"""
Task endpoint tests.

Tests cover the full lifecycle: create, list with filters,
status change, assignment, tagging, and deletion.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_USER, auth_headers, create_user


async def _setup(client: AsyncClient) -> tuple[dict, dict]:
    """Register Alice and create a project. Returns (headers, project)."""
    await create_user(client, TEST_USER)
    headers = await auth_headers(client, TEST_USER)
    r = await client.post("/api/v1/projects", json={"title": "Sprint 1"}, headers=headers)
    assert r.status_code == 201
    return headers, r.json()


async def _create_task(client: AsyncClient, headers: dict, project_id: str, **kwargs) -> dict:
    payload = {"title": "Fix bug", "priority": "medium", **kwargs}
    r = await client.post(f"/api/v1/projects/{project_id}/tasks", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_create_task(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"], title="Write tests")
    assert task["title"] == "Write tests"
    assert task["status"] == "todo"
    assert task["priority"] == "medium"


@pytest.mark.asyncio
async def test_create_task_unauthenticated(client: AsyncClient) -> None:
    _, project = await _setup(client)
    r = await client.post(f"/api/v1/projects/{project['id']}/tasks", json={"title": "t"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    await _create_task(client, headers, project["id"], title="Task A")
    await _create_task(client, headers, project["id"], title="Task B")

    r = await client.get(f"/api/v1/projects/{project['id']}/tasks", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 2


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"], title="In progress task")

    # Change the task status to in_progress.
    await client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": "in_progress"},
        headers=headers,
    )
    # Create a task that stays as todo.
    await _create_task(client, headers, project["id"], title="Todo task")

    r = await client.get(
        f"/api/v1/projects/{project['id']}/tasks?status=in_progress",
        headers=headers,
    )
    assert r.status_code == 200
    statuses = [t["status"] for t in r.json()]
    assert all(s == "in_progress" for s in statuses)


@pytest.mark.asyncio
async def test_get_task(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"])

    r = await client.get(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == task["id"]


@pytest.mark.asyncio
async def test_get_task_not_found(client: AsyncClient) -> None:
    headers, _ = await _setup(client)
    r = await client.get("/api/v1/tasks/00000000-0000-0000-0000-000000000000", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_task(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"])

    r = await client.put(
        f"/api/v1/tasks/{task['id']}",
        json={"title": "Updated title", "priority": "high"},
        headers=headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Updated title"
    assert body["priority"] == "high"


@pytest.mark.asyncio
async def test_change_task_status(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"])

    r = await client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": "done"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["status"] == "done"


@pytest.mark.asyncio
async def test_change_task_status_invalid_value(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"])

    r = await client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": "not_a_real_status"},
        headers=headers,
    )
    # Pydantic rejects unknown enum values.
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_delete_task(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"])

    r = await client.delete(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert r.status_code == 204

    r2 = await client.get(f"/api/v1/tasks/{task['id']}", headers=headers)
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_add_and_remove_tag(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"])

    # Create a tag first.
    tag_r = await client.post("/api/v1/tags", json={"name": "backend"}, headers=headers)
    assert tag_r.status_code == 201
    tag_id = tag_r.json()["id"]

    # Attach it.
    r = await client.post(f"/api/v1/tasks/{task['id']}/tags/{tag_id}", headers=headers)
    assert r.status_code == 200
    tag_names = [t["name"] for t in r.json()["tags"]]
    assert "backend" in tag_names

    # Detach it.
    r2 = await client.delete(f"/api/v1/tasks/{task['id']}/tags/{tag_id}", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["tags"] == []


@pytest.mark.asyncio
async def test_assign_task(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"])

    # Get the user's own ID from /me to use as assignee.
    me_r = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_r.json()["id"]

    r = await client.patch(
        f"/api/v1/tasks/{task['id']}/assign",
        json={"assignee_id": user_id},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["assignee_id"] == user_id


@pytest.mark.asyncio
async def test_unassign_task(client: AsyncClient) -> None:
    headers, project = await _setup(client)
    task = await _create_task(client, headers, project["id"])

    me_r = await client.get("/api/v1/users/me", headers=headers)
    user_id = me_r.json()["id"]

    # First assign.
    await client.patch(
        f"/api/v1/tasks/{task['id']}/assign",
        json={"assignee_id": user_id},
        headers=headers,
    )
    # Then unassign by sending null.
    r = await client.patch(
        f"/api/v1/tasks/{task['id']}/assign",
        json={"assignee_id": None},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["assignee_id"] is None
