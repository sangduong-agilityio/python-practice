"""
tests/test_task_due_date_filters_api.py
---------------------------------------
GET /projects/{id}/tasks with overdue, due_after and due_before
(epic E2, sub-PR feat/task-due-date-filters/endpoint).

Overdue depends on the real clock here, so the dates are far in the past (2020)
or far in the future (2099).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_comments import make_user
from tests.test_tasks import create_project


async def add_task(client, headers, project_id, title, due=None, status=None) -> dict:
    body = {"title": title}
    if due:
        body["due_date"] = due
    r = await client.post(
        f"/api/v1/projects/{project_id}/tasks", json=body, headers=headers
    )
    assert r.status_code == 201, r.text
    task = r.json()
    if status:
        r = await client.patch(
            f"/api/v1/tasks/{task['id']}/status",
            json={"status": status},
            headers=headers,
        )
        assert r.status_code == 200, r.text
    return task


@pytest.fixture
async def board(client: AsyncClient, auth_headers: dict) -> dict:
    project = await create_project(client, auth_headers, title="Due date board")
    pid = project["id"]
    await add_task(client, auth_headers, pid, "late todo", "2020-03-10T09:00:00Z")
    await add_task(
        client,
        auth_headers,
        pid,
        "late in progress",
        "2020-03-20T09:00:00Z",
        "in_progress",
    )
    await add_task(
        client, auth_headers, pid, "late but done", "2020-03-15T09:00:00Z", "done"
    )
    await add_task(client, auth_headers, pid, "future", "2099-01-15T09:00:00Z")
    await add_task(client, auth_headers, pid, "undated")
    return {"url": f"/api/v1/projects/{pid}/tasks", "headers": auth_headers}


async def titles(client, board, query) -> set[str]:
    r = await client.get(f"{board['url']}?{query}", headers=board["headers"])
    assert r.status_code == 200, r.text
    return {t["title"] for t in r.json()}


async def test_overdue_true(client, board) -> None:
    assert await titles(client, board, "overdue=true") == {
        "late todo",
        "late in progress",
    }


async def test_overdue_false_returns_everything(client, board) -> None:
    assert len(await titles(client, board, "overdue=false")) == 5


async def test_inclusive_date_range(client, board) -> None:
    found = await titles(client, board, "due_after=2020-03-10&due_before=2020-03-15")
    assert found == {"late todo", "late but done"}


async def test_due_after_alone_and_due_before_alone(client, board) -> None:
    assert await titles(client, board, "due_after=2050-01-01") == {"future"}
    assert await titles(client, board, "due_before=2020-03-14") == {"late todo"}


async def test_due_filters_combine_with_status(client, board) -> None:
    found = await titles(client, board, "due_before=2020-12-31&status=DONE")
    assert found == {"late but done"}


async def test_same_day_range_is_allowed(client, board) -> None:
    assert await titles(
        client, board, "due_after=2020-03-10&due_before=2020-03-10"
    ) == {"late todo"}


@pytest.mark.parametrize(
    "query",
    [
        "due_after=2020-03-16&due_before=2020-03-15",  # reversed range
        "due_after=15-03-2020",  # not YYYY-MM-DD
        "due_before=2020-02-30",  # no such day
        "overdue=maybe",
    ],
)
async def test_invalid_filters_are_422(client, board, query: str) -> None:
    r = await client.get(f"{board['url']}?{query}", headers=board["headers"])
    assert r.status_code == 422


async def test_reversed_range_message_names_both_dates(client, board) -> None:
    r = await client.get(
        f"{board['url']}?due_after=2020-03-16&due_before=2020-03-15",
        headers=board["headers"],
    )
    assert "2020-03-16" in r.json()["detail"] and "2020-03-15" in r.json()["detail"]


async def test_other_users_project_is_403(
    client: AsyncClient, board, db_session: AsyncSession
) -> None:
    _, other_headers = await make_user(db_session, "not_the_owner")
    r = await client.get(f"{board['url']}?overdue=true", headers=other_headers)
    assert r.status_code == 403


async def test_missing_project_is_404(client: AsyncClient, auth_headers: dict) -> None:
    r = await client.get(
        "/api/v1/projects/999999/tasks?overdue=true", headers=auth_headers
    )
    assert r.status_code == 404


async def test_no_token_is_401(client: AsyncClient, board) -> None:
    r = await client.get(f"{board['url']}?overdue=true")
    assert r.status_code == 401
