"""
tests/test_task_due_date_filters_repository.py
----------------------------------------------
Due-date filters in TaskRepository.list_by_project
(epic E2, sub-PR feat/task-due-date-filters/repository).
"""

from datetime import UTC, date, datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.repositories.task_repository import TaskRepository

NOW = datetime(2026, 12, 15, 12, 0, tzinfo=UTC)


def at(y, m, d, hh=12, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=UTC)


@pytest.fixture
async def project_id(db_session: AsyncSession, test_user: User) -> int:
    project = Project(title="Due dates", owner_id=test_user.id)
    db_session.add(project)
    await db_session.flush()
    return project.id


async def add(db_session, project_id, title, due=None, status=TaskStatus.TODO) -> Task:
    task = Task(title=title, project_id=project_id, due_date=due, status=status)
    db_session.add(task)
    await db_session.flush()
    return task


async def titles(db_session, project_id, **filters) -> set[str]:
    repo = TaskRepository(db_session)
    tasks = await repo.list_by_project(project_id, limit=100, now=NOW, **filters)
    return {t.title for t in tasks}


async def test_overdue_means_past_due_and_not_done(db_session, project_id) -> None:
    await add(db_session, project_id, "late todo", at(2026, 12, 14))
    await add(
        db_session,
        project_id,
        "late in progress",
        at(2026, 12, 1),
        TaskStatus.IN_PROGRESS,
    )
    await add(db_session, project_id, "late but done", at(2026, 12, 1), TaskStatus.DONE)
    await add(db_session, project_id, "due later today", at(2026, 12, 15, 18))
    await add(db_session, project_id, "no due date")

    assert await titles(db_session, project_id, overdue=True) == {
        "late todo",
        "late in progress",
    }


async def test_overdue_false_does_not_filter(db_session, project_id) -> None:
    await add(db_session, project_id, "late", at(2026, 12, 1))
    await add(db_session, project_id, "undated")

    assert await titles(db_session, project_id, overdue=False) == {"late", "undated"}


async def test_due_range_is_inclusive_on_both_days(db_session, project_id) -> None:
    await add(db_session, project_id, "day before start", at(2026, 11, 30, 23, 59))
    await add(db_session, project_id, "start of first day", at(2026, 12, 1, 0, 0))
    await add(db_session, project_id, "middle", at(2026, 12, 15))
    await add(db_session, project_id, "end of last day", at(2026, 12, 31, 23, 30))
    await add(db_session, project_id, "day after end", at(2027, 1, 1, 0, 0))
    await add(db_session, project_id, "undated")

    found = await titles(
        db_session,
        project_id,
        due_after=date(2026, 12, 1),
        due_before=date(2026, 12, 31),
    )
    assert found == {"start of first day", "middle", "end of last day"}


async def test_each_range_end_works_alone(db_session, project_id) -> None:
    await add(db_session, project_id, "november", at(2026, 11, 20))
    await add(db_session, project_id, "december", at(2026, 12, 20))
    await add(db_session, project_id, "undated")

    assert await titles(db_session, project_id, due_after=date(2026, 12, 1)) == {
        "december"
    }
    assert await titles(db_session, project_id, due_before=date(2026, 11, 30)) == {
        "november"
    }


async def test_due_filters_combine_with_status_and_each_other(
    db_session, project_id
) -> None:
    await add(db_session, project_id, "late todo", at(2026, 12, 10))
    await add(
        db_session,
        project_id,
        "late in progress",
        at(2026, 12, 10),
        TaskStatus.IN_PROGRESS,
    )
    await add(db_session, project_id, "late last month", at(2026, 11, 10))

    found = await titles(
        db_session,
        project_id,
        overdue=True,
        due_after=date(2026, 12, 1),
        status=TaskStatus.IN_PROGRESS,
    )
    assert found == {"late in progress"}
