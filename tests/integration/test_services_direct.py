import pytest

from app.core.exceptions import (
    PermissionDeniedException,
    ResourceAlreadyExistsException,
    ResourceNotFoundException,
)
from app.models.task import TaskPriority, TaskStatus
from app.schemas.task import TaskAssignUpdate, TaskCreate, TaskStatusUpdate, TaskUpdate
from app.schemas.user import UserCreate, UserUpdate
from app.services.task_service import TaskService
from app.services.user_service import UserService


@pytest.mark.asyncio
async def test_task_service_direct_coverage(db_session):
    """
    Hit core TaskService edge cases directly without going through the API router.
    """
    user_svc = UserService(db_session)

    # set up a dummy user
    user_data = UserCreate(email="service_task@example.com",
                           username="service_task", password="password123")
    user = await user_svc.register(user_data)

    # tests need a project to house the tasks
    from app.schemas.project import ProjectCreate
    from app.services.project_service import ProjectService
    proj_svc = ProjectService(db_session)
    project = await proj_svc.create(ProjectCreate(title="Test Proj"), user)

    task_svc = TaskService(db_session)

    # ensure basic creation works
    task = await task_svc.create(project.id, TaskCreate(title="Task 1", priority=TaskPriority.HIGH), user)
    assert task.title == "Task 1"

    # querying garbage ids should fail cleanly
    with pytest.raises(ResourceNotFoundException):
        await task_svc.get_or_404(9999)

    # test missing projects edge case by intentionally breaking the foreign key
    task.project_id = 99999
    with pytest.raises(ResourceNotFoundException):
        await task_svc.assert_project_access(task, user)
    task.project_id = project.id  # reset

    # verify another user can't access or monkey with this task
    user_data_2 = UserCreate(email="thief@example.com",
                             username="thief", password="password123")
    user_2 = await user_svc.register(user_data_2)
    with pytest.raises(PermissionDeniedException):
        await task_svc.assert_project_access(task, user_2)

    # no-op update should just return the task
    updated = await task_svc.update(task.id, TaskUpdate(), user)
    assert updated.title == "Task 1"

    # update status only
    await task_svc.change_status(task.id, TaskStatusUpdate(status=TaskStatus.DONE), user)

    # check that project scope limits visibility
    tasks = await task_svc.list_for_project(project.id, user, limit=1)
    assert len(tasks) == 1

    # bob shouldn't see alice's projects
    with pytest.raises(PermissionDeniedException):
        await task_svc.list_for_project(project.id, user_2)

    with pytest.raises(ResourceNotFoundException):
        await task_svc.list_for_project(9999, user)

    # run assign logic and make sure invalid assignment fails
    await task_svc.assign(task.id, TaskAssignUpdate(assignee_id=user_2.id), user)
    with pytest.raises(ResourceNotFoundException):
        await task_svc.assign(task.id, TaskAssignUpdate(assignee_id=9999), user)

    # clean up and verify it's gone
    await task_svc.delete(task.id, user)
    with pytest.raises(ResourceNotFoundException):
        await task_svc.get_or_404(task.id)


@pytest.mark.asyncio
async def test_user_service_direct_coverage(db_session):
    """
    Ensure the UserService handles duplicates and updates smoothly at the DB level.
    """
    user_svc = UserService(db_session)

    user_data = UserCreate(email="direct_user@example.com",
                           username="direct_user", password="password123")
    user = await user_svc.register(user_data)

    # prevent duplicate emails
    with pytest.raises(ResourceAlreadyExistsException):
        await user_svc.register(UserCreate(email="direct_user@example.com", username="other_user", password="password123"))

    # prevent duplicate usernames
    with pytest.raises(ResourceAlreadyExistsException):
        await user_svc.register(UserCreate(email="other_email@example.com", username="direct_user", password="password123"))

    # simple profile update sanity check
    updated = await user_svc.update_profile(user, UserUpdate(email="updated_email@example.com", username="updated_username"))
    assert updated.email == "updated_email@example.com"

    # blank update should not explode
    updated2 = await user_svc.update_profile(user, UserUpdate())
    assert updated2.id == user.id
