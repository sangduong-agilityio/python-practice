"""
tests/test_mcp_server.py
------------------------
Exercises the MCP server's tools, resource and prompt against the in-process
API (same test client and database as the other tests), without starting a
subprocess or a real HTTP server.
"""

import json

import pytest
from httpx import AsyncClient
from mcp.server.mcpserver.exceptions import ToolError

from mcp_server import task_api_server as srv
from tests.test_tasks import create_project, create_task


@pytest.fixture
def mcp_api(client: AsyncClient, auth_headers: dict) -> srv.TaskApiClient:
    api = srv.TaskApiClient(http=client, headers=auth_headers)
    srv.set_api(api)
    yield api
    srv.set_api(None)  # type: ignore[arg-type]


def _payload(result) -> object:
    """Read a CallToolResult: structured content when present, else the text."""
    assert not result.is_error, result.content
    if result.structured_content is not None:
        data = result.structured_content
        return data.get("result", data)
    return json.loads(result.content[0].text)


async def test_server_exposes_expected_tools_resource_and_prompt() -> None:
    tools = {t.name for t in await srv.server.list_tools()}
    assert tools == {"list_projects", "list_tasks", "create_task", "update_task_status"}
    templates = [t.uri_template for t in await srv.server.list_resource_templates()]
    assert "tasks://projects/{project_id}/tasks" in templates
    assert "standup" in {p.name for p in await srv.server.list_prompts()}


async def test_create_list_and_update_task_through_mcp(
    client: AsyncClient, auth_headers: dict, mcp_api: srv.TaskApiClient
) -> None:
    project = await create_project(client, auth_headers, title="MCP Project")

    projects = _payload(await srv.server.call_tool("list_projects", {}))
    assert any(p["id"] == project["id"] for p in projects)

    created = _payload(
        await srv.server.call_tool(
            "create_task",
            {
                "project_id": project["id"],
                "title": "Write MCP docs",
                "priority": "HIGH",
            },
        )
    )
    assert created["title"] == "Write MCP docs"
    assert created["priority"] == "high"
    assert created["status"] == "todo"

    updated = _payload(
        await srv.server.call_tool(
            "update_task_status", {"task_id": created["id"], "status": "in_progress"}
        )
    )
    assert updated["status"] == "in_progress"

    in_progress = _payload(
        await srv.server.call_tool(
            "list_tasks", {"project_id": project["id"], "status": "in_progress"}
        )
    )
    assert [t["id"] for t in in_progress] == [created["id"]]


async def test_api_errors_come_back_as_tool_errors(mcp_api: srv.TaskApiClient) -> None:
    # A ToolError's message is what an MCP client receives as the is_error result,
    # so Claude sees the API's own explanation and can correct its call.
    with pytest.raises(ToolError, match="API error 404: Task 999999 not found"):
        await srv.server.call_tool(
            "update_task_status", {"task_id": 999999, "status": "done"}
        )


async def test_project_tasks_resource_returns_json(
    client: AsyncClient, auth_headers: dict, mcp_api: srv.TaskApiClient
) -> None:
    project = await create_project(client, auth_headers, title="Resource Project")
    await create_task(client, auth_headers, project["id"], title="Read me")

    contents = list(
        await srv.server.read_resource(f"tasks://projects/{project['id']}/tasks")
    )
    tasks = json.loads(contents[0].content)
    assert [t["title"] for t in tasks] == ["Read me"]


async def test_standup_prompt_mentions_the_project() -> None:
    result = await srv.server.get_prompt("standup", {"project_id": "7"})
    text = result.messages[0].content.text
    assert "project 7" in text
    assert "list_tasks" in text
