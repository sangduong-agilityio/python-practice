"""
mcp_server/task_api_server.py
-----------------------------
An MCP server that lets Claude (Claude Code, Claude Desktop, any MCP client)
manage tasks through the running Task Management API.

It talks to the API over HTTP, exactly like any other client, so all business
rules, validation and ownership checks stay in the API.

    Tools     (Claude decides when to call): list_projects, list_tasks,
                                             create_task, update_task_status
    Resource  (the app reads it):            tasks://projects/{project_id}/tasks
    Prompt    (the user picks it):           standup

Configuration (environment variables):
    TASK_API_URL       base URL of the API      (default http://127.0.0.1:8000)
    TASK_API_EMAIL     login email of the user the server acts as
    TASK_API_PASSWORD  that user's password

Run with the stdio transport (what Claude Code uses):
    python -m mcp_server.task_api_server
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

API_PREFIX = "/api/v1"
STATUSES = ("todo", "in_progress", "done")
PRIORITIES = ("low", "medium", "high")


class TaskApiError(ToolError):
    """The API answered with an error.

    Subclassing ToolError marks it as a deliberate error, so the MCP SDK sends
    its message to Claude (other exceptions are hidden as a generic failure).
    """


class TaskApiClient:
    """Minimal async client for the Task Management API."""

    def __init__(
        self,
        http: httpx.AsyncClient,
        email: str | None = None,
        password: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.http = http
        self.email = email
        self.password = password
        self.headers = dict(headers or {})

    @classmethod
    def from_env(cls) -> TaskApiClient:
        base_url = os.environ.get("TASK_API_URL", "http://127.0.0.1:8000")
        return cls(
            http=httpx.AsyncClient(base_url=base_url, timeout=30),
            email=os.environ.get("TASK_API_EMAIL"),
            password=os.environ.get("TASK_API_PASSWORD"),
        )

    async def _login(self) -> None:
        if not (self.email and self.password):
            raise TaskApiError(
                "Set TASK_API_EMAIL and TASK_API_PASSWORD for the MCP server."
            )
        # The login endpoint takes OAuth2 form data, not JSON.
        response = await self.http.post(
            f"{API_PREFIX}/auth/login",
            data={"username": self.email, "password": self.password},
        )
        if response.status_code != 200:
            raise TaskApiError(
                f"Login failed ({response.status_code}): {response.text}"
            )
        self.headers["Authorization"] = f"Bearer {response.json()['access_token']}"

    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        if "Authorization" not in self.headers:
            await self._login()
        response = await self.http.request(
            method, f"{API_PREFIX}{path}", headers=self.headers, **kwargs
        )
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except ValueError:
                detail = response.text
            raise TaskApiError(f"API error {response.status_code}: {detail}")
        return response.json() if response.content else None


_api: TaskApiClient | None = None


def set_api(api: TaskApiClient) -> None:
    """Swap the API client (used by tests to point at the in-process app)."""
    global _api
    _api = api


def api() -> TaskApiClient:
    global _api
    if _api is None:
        _api = TaskApiClient.from_env()
    return _api


def _task_summary(task: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "id",
        "title",
        "status",
        "priority",
        "due_date",
        "assignee_id",
        "project_id",
    )
    return {k: task.get(k) for k in keys}


server = MCPServer(
    name="task-management-api",
    instructions=(
        "Manage projects and tasks in the Task Management API. "
        "Call list_projects first to find project ids. "
        f"Task status is one of {STATUSES}; priority is one of {PRIORITIES}."
    ),
)


# ---------------------------------------------------------------- tools


@server.tool(
    description="List the projects of the current user (id, title, description)."
)
async def list_projects() -> list[dict[str, Any]]:
    projects = await api().request("GET", "/projects")
    return [{k: p.get(k) for k in ("id", "title", "description")} for p in projects]


@server.tool(
    description=(
        "List the tasks of a project, optionally filtered by status "
        f"({', '.join(STATUSES)}). Returns id, title, status, priority, due date."
    )
)
async def list_tasks(
    project_id: int, status: str | None = None
) -> list[dict[str, Any]]:
    params = {"status": status} if status else None
    tasks = await api().request("GET", f"/projects/{project_id}/tasks", params=params)
    return [_task_summary(t) for t in tasks]


@server.tool(
    description=(
        "Create a task in a project. priority is low, medium or high (default medium). "
        "Returns the created task."
    )
)
async def create_task(
    project_id: int,
    title: str,
    description: str | None = None,
    priority: str = "medium",
) -> dict[str, Any]:
    body = {"title": title, "description": description, "priority": priority}
    task = await api().request("POST", f"/projects/{project_id}/tasks", json=body)
    return _task_summary(task)


@server.tool(
    description=f"Change the status of a task to one of {', '.join(STATUSES)}. Returns the task."
)
async def update_task_status(task_id: int, status: str) -> dict[str, Any]:
    task = await api().request(
        "PATCH", f"/tasks/{task_id}/status", json={"status": status}
    )
    return _task_summary(task)


# ---------------------------------------------------------------- resource


@server.resource(
    "tasks://projects/{project_id}/tasks",
    name="project-tasks",
    description="All tasks of one project as JSON (for @-mentioning a project).",
    mime_type="application/json",
)
async def project_tasks(project_id: str) -> str:
    tasks = await api().request("GET", f"/projects/{int(project_id)}/tasks")
    return json.dumps([_task_summary(t) for t in tasks], indent=2)


# ---------------------------------------------------------------- prompt


@server.prompt(
    name="standup",
    description="Write a short daily stand-up summary for one project.",
)
def standup(project_id: str) -> str:
    return (
        f"Write a daily stand-up summary for project {project_id}.\n"
        "1. Call list_tasks for the project to get every task.\n"
        "2. Group them into three sections: Done, In progress, To do.\n"
        "3. Under To do, list high-priority tasks first and flag any task whose "
        "due date has passed.\n"
        "4. End with one line naming the single most important next task.\n"
        "Keep it under 15 lines and only use data returned by the tools."
    )


def main() -> None:
    # stdout carries the MCP messages over stdio; anything for humans goes to stderr.
    print("task-management-api MCP server starting (stdio)", file=sys.stderr)
    server.run("stdio")


if __name__ == "__main__":
    main()
