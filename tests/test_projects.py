"""
Project endpoint tests.

Covers ownership isolation -- a user must not be able to read,
update, or delete another user's projects.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import SECOND_USER, TEST_USER, auth_headers, create_user


async def _create_project(client: AsyncClient, headers: dict, title: str = "My Project") -> dict:
    r = await client.post("/api/v1/projects", json={"title": title}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.mark.asyncio
async def test_create_project(client: AsyncClient) -> None:
    await create_user(client)
    headers = await auth_headers(client)
    project = await _create_project(client, headers)
    assert project["title"] == "My Project"
    assert "id" in project


@pytest.mark.asyncio
async def test_create_project_unauthenticated(client: AsyncClient) -> None:
    r = await client.post("/api/v1/projects", json={"title": "No auth"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_projects_only_own(client: AsyncClient) -> None:
    # Alice creates a project.
    await create_user(client, TEST_USER)
    alice_headers = await auth_headers(client, TEST_USER)
    await _create_project(client, alice_headers, title="Alice project")

    # Bob creates a project.
    await create_user(client, SECOND_USER)
    bob_headers = await auth_headers(client, SECOND_USER)
    await _create_project(client, bob_headers, title="Bob project")

    # Alice should only see her own project.
    r = await client.get("/api/v1/projects", headers=alice_headers)
    assert r.status_code == 200
    titles = [p["title"] for p in r.json()]
    assert "Alice project" in titles
    assert "Bob project" not in titles


@pytest.mark.asyncio
async def test_get_project_not_owner_returns_403(client: AsyncClient) -> None:
    await create_user(client, TEST_USER)
    alice_headers = await auth_headers(client, TEST_USER)
    project = await _create_project(client, alice_headers)

    await create_user(client, SECOND_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    r = await client.get(f"/api/v1/projects/{project['id']}", headers=bob_headers)
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient) -> None:
    await create_user(client)
    headers = await auth_headers(client)
    r = await client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000", headers=headers)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient) -> None:
    await create_user(client)
    headers = await auth_headers(client)
    project = await _create_project(client, headers)

    r = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"title": "Renamed"},
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["title"] == "Renamed"


@pytest.mark.asyncio
async def test_update_project_not_owner_returns_403(client: AsyncClient) -> None:
    await create_user(client, TEST_USER)
    alice_headers = await auth_headers(client, TEST_USER)
    project = await _create_project(client, alice_headers)

    await create_user(client, SECOND_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    r = await client.put(
        f"/api/v1/projects/{project['id']}",
        json={"title": "Stolen"},
        headers=bob_headers,
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient) -> None:
    await create_user(client)
    headers = await auth_headers(client)
    project = await _create_project(client, headers)

    r = await client.delete(f"/api/v1/projects/{project['id']}", headers=headers)
    assert r.status_code == 204

    # Verify it is actually gone.
    r2 = await client.get(f"/api/v1/projects/{project['id']}", headers=headers)
    assert r2.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_not_owner_returns_403(client: AsyncClient) -> None:
    await create_user(client, TEST_USER)
    alice_headers = await auth_headers(client, TEST_USER)
    project = await _create_project(client, alice_headers)

    await create_user(client, SECOND_USER)
    bob_headers = await auth_headers(client, SECOND_USER)

    r = await client.delete(f"/api/v1/projects/{project['id']}", headers=bob_headers)
    assert r.status_code == 403
