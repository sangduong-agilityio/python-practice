"""
tests/test_projects.py
-----------------------
Tests for Project CRUD endpoints.

Covers: happy path, auth failure (401), not found (404),
forbidden (403), and validation error (422).
"""

import pytest
from httpx import AsyncClient

from app.models.user import User
from app.core.security import create_access_token


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def create_project(client: AsyncClient, headers: dict, title: str = "My Project") -> dict:
    """Utility to create a project and return the response JSON."""
    r = await client.post(
        "/api/v1/projects",
        json={"title": title, "description": "A test project"},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


# ---------------------------------------------------------------------------
# Create project
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient, auth_headers: dict) -> None:
    """Authenticated user can create a project."""
    response = await client.post(
        "/api/v1/projects",
        json={"title": "Work Tasks", "description": "All work-related tasks"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Work Tasks"
    assert "id" in data
    assert "owner_id" in data


@pytest.mark.asyncio
async def test_create_project_no_auth_401(client: AsyncClient) -> None:
    """Creating a project without auth returns 401."""
    response = await client.post("/api/v1/projects", json={"title": "Test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_project_empty_title_422(client: AsyncClient, auth_headers: dict) -> None:
    """Empty title fails Pydantic validation (422)."""
    response = await client.post(
        "/api/v1/projects",
        json={"title": ""},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List projects
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_projects_returns_only_own(
    client: AsyncClient, auth_headers: dict, db_session
) -> None:
    """User can only see their own projects."""
    # Create a project as the test user
    await create_project(client, auth_headers, "My Project")

    # Create a second user and their project
    other_user = User(
        email="other@example.com",
        username="otheruser",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()
    await db_session.refresh(other_user)

    other_token = create_access_token({"sub": str(other_user.id)})
    other_headers = {"Authorization": f"Bearer {other_token}"}
    await create_project(client, other_headers, "Other's Project")

    # Test user should only see their own project
    response = await client.get("/api/v1/projects", headers=auth_headers)
    assert response.status_code == 200
    titles = [p["title"] for p in response.json()]
    assert "My Project" in titles
    assert "Other's Project" not in titles


@pytest.mark.asyncio
async def test_list_projects_pagination(client: AsyncClient, auth_headers: dict) -> None:
    """Pagination parameters (skip, limit) work correctly."""
    for i in range(5):
        await create_project(client, auth_headers, f"Project {i}")

    response = await client.get("/api/v1/projects?skip=0&limit=2", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) <= 2


# ---------------------------------------------------------------------------
# Get single project
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_project_success(client: AsyncClient, auth_headers: dict) -> None:
    """Fetching an existing project by ID returns it."""
    project = await create_project(client, auth_headers)
    response = await client.get(f"/api/v1/projects/{project['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["id"] == project["id"]


@pytest.mark.asyncio
async def test_get_project_not_found_404(client: AsyncClient, auth_headers: dict) -> None:
    """Fetching a non-existent project ID returns 404."""
    response = await client.get("/api/v1/projects/999999", headers=auth_headers)
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Update project
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_update_project_success(client: AsyncClient, auth_headers: dict) -> None:
    """Owner can update their project's title."""
    project = await create_project(client, auth_headers)
    response = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"title": "Updated Title"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_update_project_forbidden_403(
    client: AsyncClient, auth_headers: dict, db_session
) -> None:
    """Non-owner cannot update a project (403 Forbidden)."""
    # Create a project as test user
    project = await create_project(client, auth_headers)

    # Create another user and try to update the project
    other_user = User(
        email="evil@example.com",
        username="eviluser",
        hashed_password="hashed",
        is_active=True,
    )
    db_session.add(other_user)
    await db_session.flush()
    await db_session.refresh(other_user)

    evil_token = create_access_token({"sub": str(other_user.id)})
    evil_headers = {"Authorization": f"Bearer {evil_token}"}

    response = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"title": "Hacked!"},
        headers=evil_headers,
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# Delete project
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_delete_project_success(client: AsyncClient, auth_headers: dict) -> None:
    """Owner can delete their project (returns 204)."""
    project = await create_project(client, auth_headers)
    response = await client.delete(
        f"/api/v1/projects/{project['id']}", headers=auth_headers
    )
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(
        f"/api/v1/projects/{project['id']}", headers=auth_headers
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_found_404(client: AsyncClient, auth_headers: dict) -> None:
    """Deleting a non-existent project returns 404."""
    response = await client.delete("/api/v1/projects/999999", headers=auth_headers)
    assert response.status_code == 404
