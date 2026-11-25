"""
tests/test_comments.py
----------------------
Tests for the task comments API: create and list (epic E1).
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password
from app.models.task_comment import TaskComment
from app.models.user import User

# ---------------------------------------------------------------------------
# Helpers & fixtures
# ---------------------------------------------------------------------------


async def create_project(
    client: AsyncClient, headers: dict, title: str = "Comment Project"
) -> dict:
    r = await client.post("/api/v1/projects", json={"title": title}, headers=headers)
    assert r.status_code == 201
    return r.json()


async def create_task(client: AsyncClient, headers: dict, project_id: int) -> dict:
    r = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={"title": "Task with comments"},
        headers=headers,
    )
    assert r.status_code == 201
    return r.json()


async def make_user(
    db_session: AsyncSession, username: str
) -> tuple[User, dict[str, str]]:
    user = User(
        email=f"{username}@example.com",
        username=username,
        hashed_password=hash_password("testpassword123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    token = create_access_token(data={"sub": str(user.id)})
    return user, {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def other_user(db_session: AsyncSession) -> tuple[User, dict[str, str]]:
    """A second user who is neither project owner nor assignee by default."""
    return await make_user(db_session, "commenter_other")


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_owner_can_create_comment(
    client: AsyncClient, auth_headers: dict, test_user: User
) -> None:
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.post(
        f"/api/v1/tasks/{task['id']}/comments",
        json={"content": "  First comment  "},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "First comment"  # whitespace trimmed
    assert data["task_id"] == task["id"]
    assert data["author_id"] == test_user.id
    assert "id" in data and "created_at" in data and "updated_at" in data


@pytest.mark.asyncio
async def test_assignee_can_create_comment(
    client: AsyncClient, auth_headers: dict, other_user: tuple[User, dict[str, str]]
) -> None:
    assignee, assignee_headers = other_user
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    assign = await client.patch(
        f"/api/v1/tasks/{task['id']}/assign",
        json={"assignee_id": assignee.id},
        headers=auth_headers,
    )
    assert assign.status_code == 200

    response = await client.post(
        f"/api/v1/tasks/{task['id']}/comments",
        json={"content": "Working on it"},
        headers=assignee_headers,
    )
    assert response.status_code == 201
    assert response.json()["author_id"] == assignee.id


@pytest.mark.asyncio
@pytest.mark.parametrize("content", ["", "   "])
async def test_create_comment_blank_content_422(
    client: AsyncClient, auth_headers: dict, content: str
) -> None:
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.post(
        f"/api/v1/tasks/{task['id']}/comments",
        json={"content": content},
        headers=auth_headers,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_comments(client: AsyncClient, auth_headers: dict) -> None:
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])
    for text in ("one", "two", "three"):
        r = await client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={"content": text},
            headers=auth_headers,
        )
        assert r.status_code == 201

    response = await client.get(
        f"/api/v1/tasks/{task['id']}/comments", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert [c["content"] for c in data["items"]] == [
        "one",
        "two",
        "three",
    ]  # oldest first


@pytest.mark.asyncio
async def test_list_comments_pagination(
    client: AsyncClient, auth_headers: dict
) -> None:
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])
    for i in range(5):
        await client.post(
            f"/api/v1/tasks/{task['id']}/comments",
            json={"content": f"comment {i}"},
            headers=auth_headers,
        )

    response = await client.get(
        f"/api/v1/tasks/{task['id']}/comments?limit=2&offset=2", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert data["limit"] == 2
    assert data["offset"] == 2
    assert [c["content"] for c in data["items"]] == ["comment 2", "comment 3"]


@pytest.mark.asyncio
async def test_list_excludes_soft_deleted(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, test_user: User
) -> None:
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])
    await client.post(
        f"/api/v1/tasks/{task['id']}/comments",
        json={"content": "visible"},
        headers=auth_headers,
    )
    db_session.add(
        TaskComment(
            task_id=task["id"],
            author_id=test_user.id,
            content="hidden",
            is_deleted=True,
        )
    )
    await db_session.flush()

    response = await client.get(
        f"/api/v1/tasks/{task['id']}/comments", headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert [c["content"] for c in data["items"]] == ["visible"]


@pytest.mark.asyncio
@pytest.mark.parametrize("query", ["limit=0", "limit=101", "offset=-1"])
async def test_list_comments_invalid_pagination_422(
    client: AsyncClient, auth_headers: dict, query: str
) -> None:
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.get(
        f"/api/v1/tasks/{task['id']}/comments?{query}", headers=auth_headers
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 401 / 403 / 404
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_comments_unauthenticated_401(
    client: AsyncClient, auth_headers: dict
) -> None:
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])
    url = f"/api/v1/tasks/{task['id']}/comments"

    assert (await client.post(url, json={"content": "hi"})).status_code == 401
    assert (await client.get(url)).status_code == 401


@pytest.mark.asyncio
async def test_comments_forbidden_403(
    client: AsyncClient, auth_headers: dict, other_user: tuple[User, dict[str, str]]
) -> None:
    """A user who is neither project owner nor assignee gets 403 on POST and GET."""
    _, outsider_headers = other_user
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])
    url = f"/api/v1/tasks/{task['id']}/comments"

    post = await client.post(url, json={"content": "sneaky"}, headers=outsider_headers)
    assert post.status_code == 403
    get = await client.get(url, headers=outsider_headers)
    assert get.status_code == 403


@pytest.mark.asyncio
async def test_comments_task_not_found_404(
    client: AsyncClient, auth_headers: dict
) -> None:
    url = "/api/v1/tasks/999999/comments"

    post = await client.post(url, json={"content": "hi"}, headers=auth_headers)
    assert post.status_code == 404
    get = await client.get(url, headers=auth_headers)
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_create_comment_too_long_422(
    client: AsyncClient, auth_headers: dict
) -> None:
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])

    response = await client.post(
        f"/api/v1/tasks/{task['id']}/comments",
        json={"content": "x" * 5001},
        headers=auth_headers,
    )
    assert response.status_code == 422
