"""
tests/test_day02_bug_reproduce.py
---------------------------------
Regression test for TICKET-201 (originally a seeded bug for Day 02).

Bug Summary:
Clients sending status query parameter in uppercase (e.g., status=TODO or status=IN_PROGRESS)
used to fail validation (HTTP 422) instead of being accepted with case-insensitive
normalization (HTTP 200).

The bug is fixed: the list endpoint normalizes `status` with `.strip().lower()` before
parsing the enum. This test guards against it coming back, and is expected to PASS (Green).
"""

import pytest
from httpx import AsyncClient

from tests.test_tasks import create_project, create_task


@pytest.mark.asyncio
async def test_reproduce_ticket_201_case_insensitive_status_filter(
    client: AsyncClient, auth_headers: dict
) -> None:
    """
    Regression test for TICKET-201:
    Assert that the endpoint accepts uppercase status parameters (e.g. ?status=TODO)
    and returns HTTP 200 with the matching tasks.
    """
    # 1. Setup: Create a project and a task
    project = await create_project(client, auth_headers, title="Day 02 Repro Project")
    task = await create_task(client, auth_headers, project["id"], title="Bug Repro Task")

    # 2. Trigger: Call GET endpoint with uppercase status 'TODO'
    response = await client.get(
        f"/api/v1/projects/{project['id']}/tasks?status=TODO",
        headers=auth_headers,
    )

    # 3. Verification:
    # Expected: HTTP 200 with the filtered task list (case-insensitive)
    # Current buggy behavior: Fails with HTTP 422 because enum only recognizes 'todo'
    assert response.status_code == 200, (
        f"BUG REPRODUCED! Expected 200 OK with case-insensitive matching, "
        f"but API returned {response.status_code}: {response.json()}"
    )

    data = response.json()
    assert len(data) >= 1
    assert data[0]["status"] == "todo"
