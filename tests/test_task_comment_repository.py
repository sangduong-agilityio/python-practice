"""
tests/test_task_comment_repository.py
-------------------------------------
Repository tests for task comments (epic E1, sub-PR feat/task-comments/model).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.repositories.task_comment_repository import TaskCommentRepository


@pytest.fixture
async def task(db_session: AsyncSession, test_user: User) -> Task:
    project = Project(title="Comments project", owner_id=test_user.id)
    db_session.add(project)
    await db_session.flush()
    task = Task(title="Discuss me", project_id=project.id)
    db_session.add(task)
    await db_session.flush()
    await db_session.refresh(task)
    return task


async def test_create_sets_defaults(db_session, test_user, task) -> None:
    repo = TaskCommentRepository(db_session)
    comment = await repo.create(task.id, test_user.id, "First!")

    assert comment.id is not None
    assert comment.task_id == task.id
    assert comment.author_id == test_user.id
    assert comment.content == "First!"
    assert comment.is_deleted is False
    assert comment.created_at is not None


async def test_list_is_oldest_first_and_paginated(db_session, test_user, task) -> None:
    repo = TaskCommentRepository(db_session)
    for n in range(5):
        await repo.create(task.id, test_user.id, f"comment {n}")

    first_page = await repo.list_by_task(task.id, limit=2, offset=0)
    second_page = await repo.list_by_task(task.id, limit=2, offset=2)

    assert [c.content for c in first_page] == ["comment 0", "comment 1"]
    assert [c.content for c in second_page] == ["comment 2", "comment 3"]
    assert await repo.count_by_task(task.id) == 5


async def test_soft_deleted_comments_are_invisible(db_session, test_user, task) -> None:
    repo = TaskCommentRepository(db_session)
    kept = await repo.create(task.id, test_user.id, "kept")
    hidden = await repo.create(task.id, test_user.id, "hidden")
    hidden.is_deleted = True
    await db_session.flush()

    assert [c.id for c in await repo.list_by_task(task.id)] == [kept.id]
    assert await repo.count_by_task(task.id) == 1
    assert await repo.get_by_id(hidden.id) is None
    assert (await repo.get_by_id(kept.id)).content == "kept"


async def test_comments_are_scoped_to_their_task(db_session, test_user, task) -> None:
    other = Task(title="Other task", project_id=task.project_id)
    db_session.add(other)
    await db_session.flush()
    repo = TaskCommentRepository(db_session)
    await repo.create(task.id, test_user.id, "on task")
    await repo.create(other.id, test_user.id, "on other")

    assert [c.content for c in await repo.list_by_task(task.id)] == ["on task"]
    assert await repo.count_by_task(other.id) == 1
