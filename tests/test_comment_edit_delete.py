"""
tests/test_comment_edit_delete.py
---------------------------------
Edit (author only) and delete (author or project owner, soft delete) of task
comments (epic E1, sub-PR feat/task-comments/edit-delete).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_comment import TaskComment
from tests.test_comments import create_project, create_task, make_user


@pytest.fixture
async def setup(client: AsyncClient, auth_headers: dict, db_session: AsyncSession):
    """Owner's project and task, an assignee, an outsider, one comment by each member."""
    project = await create_project(client, auth_headers)
    task = await create_task(client, auth_headers, project["id"])
    assignee, assignee_headers = await make_user(db_session, "assignee_user")
    _, outsider_headers = await make_user(db_session, "outsider_user")
    assign = await client.patch(
        f"/api/v1/tasks/{task['id']}/assign",
        json={"assignee_id": assignee.id},
        headers=auth_headers,
    )
    assert assign.status_code == 200

    url = f"/api/v1/tasks/{task['id']}/comments"
    owner_comment = (
        await client.post(url, json={"content": "owner says"}, headers=auth_headers)
    ).json()
    assignee_comment = (
        await client.post(
            url, json={"content": "assignee says"}, headers=assignee_headers
        )
    ).json()
    return {
        "task": task,
        "owner": auth_headers,
        "assignee": assignee_headers,
        "outsider": outsider_headers,
        "owner_comment": owner_comment,
        "assignee_comment": assignee_comment,
        "list_url": url,
    }


# ---------------------------------------------------------------- edit


async def test_author_can_edit_own_comment(client: AsyncClient, setup) -> None:
    comment = setup["assignee_comment"]
    response = await client.patch(
        f"/api/v1/comments/{comment['id']}",
        json={"content": "  assignee says, edited  "},
        headers=setup["assignee"],
    )
    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "assignee says, edited"
    assert body["id"] == comment["id"]
    assert body["author_id"] == comment["author_id"]

    listed = (await client.get(setup["list_url"], headers=setup["owner"])).json()
    assert "assignee says, edited" in [c["content"] for c in listed["items"]]


@pytest.mark.parametrize("who", ["owner", "outsider"])
async def test_only_the_author_can_edit(client: AsyncClient, setup, who: str) -> None:
    comment = setup["assignee_comment"]
    response = await client.patch(
        f"/api/v1/comments/{comment['id']}",
        json={"content": "rewritten"},
        headers=setup[who],
    )
    assert response.status_code == 403


@pytest.mark.parametrize("content", ["", "   ", "x" * 5001])
async def test_edit_invalid_content_422(
    client: AsyncClient, setup, content: str
) -> None:
    comment = setup["owner_comment"]
    response = await client.patch(
        f"/api/v1/comments/{comment['id']}",
        json={"content": content},
        headers=setup["owner"],
    )
    assert response.status_code == 422


async def test_edit_missing_comment_404(client: AsyncClient, setup) -> None:
    response = await client.patch(
        "/api/v1/comments/999999", json={"content": "hi"}, headers=setup["owner"]
    )
    assert response.status_code == 404


# ---------------------------------------------------------------- delete


async def test_author_can_delete_own_comment(client: AsyncClient, setup) -> None:
    comment = setup["assignee_comment"]
    response = await client.delete(
        f"/api/v1/comments/{comment['id']}", headers=setup["assignee"]
    )
    assert response.status_code == 204

    listed = (await client.get(setup["list_url"], headers=setup["owner"])).json()
    assert comment["id"] not in [c["id"] for c in listed["items"]]
    assert listed["total"] == 1


async def test_project_owner_can_delete_any_comment_on_the_project(
    client: AsyncClient, setup
) -> None:
    comment = setup["assignee_comment"]
    response = await client.delete(
        f"/api/v1/comments/{comment['id']}", headers=setup["owner"]
    )
    assert response.status_code == 204


async def test_assignee_cannot_delete_someone_elses_comment(
    client: AsyncClient, setup
) -> None:
    comment = setup["owner_comment"]
    response = await client.delete(
        f"/api/v1/comments/{comment['id']}", headers=setup["assignee"]
    )
    assert response.status_code == 403


async def test_outsider_cannot_delete(client: AsyncClient, setup) -> None:
    comment = setup["owner_comment"]
    response = await client.delete(
        f"/api/v1/comments/{comment['id']}", headers=setup["outsider"]
    )
    assert response.status_code == 403


async def test_delete_is_soft_and_deleted_comments_are_gone_for_the_api(
    client: AsyncClient, setup, db_session: AsyncSession
) -> None:
    comment = setup["owner_comment"]
    url = f"/api/v1/comments/{comment['id']}"
    assert (await client.delete(url, headers=setup["owner"])).status_code == 204

    row = await db_session.get(TaskComment, comment["id"])
    assert row is not None and row.is_deleted is True  # row kept for history

    assert (await client.delete(url, headers=setup["owner"])).status_code == 404
    edit = await client.patch(url, json={"content": "back"}, headers=setup["owner"])
    assert edit.status_code == 404


async def test_edit_and_delete_require_login(client: AsyncClient, setup) -> None:
    url = f"/api/v1/comments/{setup['owner_comment']['id']}"
    assert (await client.patch(url, json={"content": "hi"})).status_code == 401
    assert (await client.delete(url)).status_code == 401
