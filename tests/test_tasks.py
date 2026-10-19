"""
tests/test_tasks.py
--------------------
Tests for Task CRUD, status changes, assignment, and tagging endpoints.
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def create_project(client: AsyncClient, headers: dict, title: str = "Test Project") -> dict:
    r = await client.post(
        "/api/v1/projects",
        json={"title": title},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


async def create_task(
    client: AsyncClient,
    headers: dict,
    project_id: int,
    title: str = "Fix bug",
) -> dict:
    r = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": title, "priority": "medium"},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


# ---------------------------------------------------------------------------
# Create task
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_task_success(client: AsyncClient, auth_headers: dict) -> None:
    """Project owner can create a task inside their project."""
    project = await create_project(client, auth_headers)
    response = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Write tests", "priority": "high"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Write tests"
    assert data["priority"] == "high"
    assert data["status"] == "todo"  # Default status
    assert data["project_id"] == project["id"]


@pytest.mark.asyncio
async def test_create_task_no_auth_401(client: AsyncClient, auth_headers: dict) -> None:
    """Creating a task without auth returns 401."""
    project = await create_project(client, auth_headers)
    response = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "No auth task"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_task_invalid_project_404(client: AsyncClient, auth_headers: dict) -> None:
    """Creating a task in a non-existent project returns 404."""
    response = await client.post(
        "/api/v1/projects/999999/tasks",
        json={"title": "Task"},
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_task_invalid_priority_422(client: AsyncClient, auth_headers: dict) -> None:
    """Invalid priority value fails Pydantic validation (422)."""
    project = await create_project(client, auth_headers)
    response = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Bad priority", "priority": "CRITICAL"},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List tasks
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_tasks_with_filters(client: AsyncClient, auth_headers: dict) -> None:
    """Tasks can be filtered by status and priority."""
    project = await create_project(client, auth_headers)

    # Create tasks with different priorities
    await create_task(client, auth_headers, project["id"], "High priority task")
    await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={"title": "Low priority task", "priority": "low"},
        headers=auth_headers,
    )

    # Filter by priority
    response = await client.get(
        f"/api/v1/projects/{project['id']}/tasks?priority=medium",
        headers=auth_headers,
    )
    assert response.status_code == 200
    tasks = response.json()
    assert all(t["priority"] == "medium" for t in tasks)


# ---------------------------------------------------------------------------
# Get single task
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_task_success(client: AsyncClient, auth_headers: dict) -> None:
    """Fetching a task by ID returns its details."""
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == task["id"]


@pytest.mark.asyncio
async def test_get_task_not_found_404(client: AsyncClient, auth_headers: dict) -> None:
    """Fetching a non-existent task returns 404."""
    response = await client.get("/api/v1/tasks/999999", headers=auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Update task
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_task_success(client: AsyncClient, auth_headers: dict) -> None:
    """Owner can update task title and description."""
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.put(
        f"/api/v1/tasks/{task['id']}",
        json={"title": "Updated task", "description": "Now with details"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated task"
    assert data["description"] == "Now with details"


# ---------------------------------------------------------------------------
# Change status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_change_task_status(client: AsyncClient, auth_headers: dict) -> None:
    """PATCH /tasks/{id}/status correctly updates the status field."""
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    assert task["status"] == "todo"  # Starts as todo

    response = await client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": "in_progress"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"

    # Move to done
    response = await client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": "done"},
        headers=auth_headers,
    )
    assert response.json()["status"] == "done"


@pytest.mark.asyncio
async def test_change_status_invalid_value_422(client: AsyncClient, auth_headers: dict) -> None:
    """Invalid status value fails validation."""
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": "not_a_real_status"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sent", "expected"),
    [("DONE", "done"), ("IN_PROGRESS", "in_progress"), ("Done", "done")],
)
async def test_change_task_status_case_insensitive(
    client: AsyncClient, auth_headers: dict, sent: str, expected: str
) -> None:
    """Status values are accepted regardless of casing (TICKET-206)."""
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": sent},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == expected


@pytest.mark.asyncio
async def test_change_status_blocked_422(client: AsyncClient, auth_headers: dict) -> None:
    """Unknown statuses such as BLOCKED are still rejected."""
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.patch(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": "BLOCKED"},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_and_attach_tag(client: AsyncClient, auth_headers: dict) -> None:
    """Create a tag, then attach it to a task."""
    # Create a tag
    tag_response = await client.post(
        "/api/v1/tags",
        json={"name": "backend", "color": "#FF5733"},
        headers=auth_headers,
    )
    assert tag_response.status_code == 201
    tag = tag_response.json()
    assert tag["name"] == "backend"

    # Create project + task
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    # Attach tag to task
    response = await client.post(
        f"/api/v1/tasks/{task['id']}/tags/{tag['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    tag_names = [t["name"] for t in response.json()["tags"]]
    assert "backend" in tag_names


@pytest.mark.asyncio
async def test_remove_tag_from_task(client: AsyncClient, auth_headers: dict) -> None:
    """Remove a tag from a task."""
    tag_r = await client.post(
        "/api/v1/tags",
        json={"name": "removable", "color": "#AABBCC"},
        headers=auth_headers,
    )
    tag = tag_r.json()

    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    # Attach
    await client.post(f"/api/v1/tasks/{task['id']}/tags/{tag['id']}", headers=auth_headers)

    # Remove
    response = await client.delete(
        f"/api/v1/tasks/{task['id']}/tags/{tag['id']}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    tag_names = [t["name"] for t in response.json()["tags"]]
    assert "removable" not in tag_names


# ---------------------------------------------------------------------------
# Delete task
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_task_success(client: AsyncClient, auth_headers: dict) -> None:
    """Owner can delete a task (returns 204)."""
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.delete(f"/api/v1/tasks/{task['id']}", headers=auth_headers)
    assert response.status_code == 204

    # Verify gone
    get_r = await client.get(f"/api/v1/tasks/{task['id']}", headers=auth_headers)
    assert get_r.status_code == 404
