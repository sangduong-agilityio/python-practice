"""
tests/test_task_search_api.py
-----------------------------
GET /projects/{id}/tasks?q=... (epic E3, sub-PR feat/task-search/endpoint).
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.test_comments import make_user
from tests.test_tasks import create_project


@pytest.fixture
async def board(client: AsyncClient, auth_headers: dict) -> dict:
    project = await create_project(client, auth_headers, title="Search board")
    url = f"/api/v1/projects/{project['id']}/tasks"
    for title, description, due in [
        (
            "Fix login timeout",
            "Users are logged out after 5 minutes",
            "2020-01-10T09:00:00Z",
        ),
        ("Write invoice export", "CSV export for the LOGIN audit", None),
        ("Release notes", None, None),
        ("Reach 100% coverage", None, None),
    ]:
        body = {"title": title, "description": description}
        if due:
            body["due_date"] = due
        r = await client.post(url, json=body, headers=auth_headers)
        assert r.status_code == 201, r.text
    return {"url": url, "headers": auth_headers}


async def titles(client, board, query) -> set[str]:
    r = await client.get(board["url"], params=query, headers=board["headers"])
    assert r.status_code == 200, r.text
    return {t["title"] for t in r.json()}


async def test_search_title_and_description(client, board) -> None:
    assert await titles(client, board, {"q": "Login"}) == {
        "Fix login timeout",
        "Write invoice export",
    }


async def test_surrounding_spaces_are_ignored(client, board) -> None:
    assert await titles(client, board, {"q": "  invoice  "}) == {"Write invoice export"}


@pytest.mark.parametrize("q", ["", "   "])
async def test_empty_search_shows_everything(client, board, q: str) -> None:
    assert len(await titles(client, board, {"q": q})) == 4


async def test_percent_is_literal(client, board) -> None:
    assert await titles(client, board, {"q": "100%"}) == {"Reach 100% coverage"}


async def test_search_combines_with_due_date_filter(client, board) -> None:
    found = await titles(client, board, {"q": "login", "overdue": "true"})
    assert found == {"Fix login timeout"}


async def test_no_match_is_empty_list(client, board) -> None:
    assert await titles(client, board, {"q": "zzz"}) == set()


async def test_query_over_100_characters_is_422(client, board) -> None:
    r = await client.get(
        board["url"], params={"q": "x" * 101}, headers=board["headers"]
    )
    assert r.status_code == 422


async def test_other_users_project_is_403(
    client: AsyncClient, board, db_session: AsyncSession
) -> None:
    _, other = await make_user(db_session, "search_outsider")
    r = await client.get(board["url"], params={"q": "login"}, headers=other)
    assert r.status_code == 403


async def test_no_token_is_401(client: AsyncClient, board) -> None:
    r = await client.get(board["url"], params={"q": "login"})
    assert r.status_code == 401
