"""
tests/test_task_search_repository.py
------------------------------------
Text search (`q`) in TaskRepository.list_by_project (epic E3, sub-PR feat/task-search/repository).
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.repositories.task_repository import TaskRepository


@pytest.fixture
async def project_id(db_session: AsyncSession, test_user: User) -> int:
    project = Project(title="Search", owner_id=test_user.id)
    db_session.add(project)
    await db_session.flush()
    for title, description, status in [
        ("Fix login timeout", "Users are logged out after 5 minutes", TaskStatus.TODO),
        ("Write invoice export", "CSV export for the LOGIN audit", TaskStatus.DONE),
        ("Release notes", None, TaskStatus.TODO),
        ("Reach 100% coverage", "tests_only", TaskStatus.TODO),
        ("Reach 100 users", "growth", TaskStatus.TODO),
    ]:
        db_session.add(
            Task(
                title=title,
                description=description,
                status=status,
                project_id=project.id,
            )
        )
    await db_session.flush()
    return project.id


async def titles(db_session, project_id, **filters) -> set[str]:
    tasks = await TaskRepository(db_session).list_by_project(
        project_id, limit=100, **filters
    )
    return {t.title for t in tasks}


async def test_matches_title_or_description_case_insensitively(
    db_session, project_id
) -> None:
    assert await titles(db_session, project_id, q="LOGIN") == {
        "Fix login timeout",  # title
        "Write invoice export",  # description
    }


async def test_matches_part_of_a_word(db_session, project_id) -> None:
    assert await titles(db_session, project_id, q="voic") == {"Write invoice export"}


async def test_null_description_does_not_break_or_match(db_session, project_id) -> None:
    assert await titles(db_session, project_id, q="notes") == {"Release notes"}


async def test_wildcards_are_literal(db_session, project_id) -> None:
    assert await titles(db_session, project_id, q="100%") == {"Reach 100% coverage"}
    assert await titles(db_session, project_id, q="s_o") == {"Reach 100% coverage"}
    assert await titles(db_session, project_id, q="%") == {"Reach 100% coverage"}


async def test_no_match_returns_empty(db_session, project_id) -> None:
    assert await titles(db_session, project_id, q="nothing like this") == set()


async def test_combines_with_other_filters(db_session, project_id) -> None:
    found = await titles(db_session, project_id, q="login", status=TaskStatus.TODO)
    assert found == {"Fix login timeout"}
