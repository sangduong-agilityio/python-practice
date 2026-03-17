"""
Tests for task service functions.
"""
import pytest
from src.fastapi_training.app.services.task_service import (
    create_task_service,
    get_tasks_for_user_service,
    get_task_by_id_service,
    update_task_service,
    delete_task_service,
    filter_tasks_by_status_service,
    search_tasks_by_title_service,
)
from src.fastapi_training.app.schemas.task import TaskCreate, TaskUpdate, TaskStatus
from src.fastapi_training.app.db.fake_db import fake_tasks_db, fake_users_db
from datetime import datetime


class TestCreateTask:
    """Tests for task creation."""

    def test_create_task_success(self, test_task_data, test_user_db):
        """Test successful task creation."""
        task_in = TaskCreate(**test_task_data)
        task = create_task_service(task_in, test_user_db["id"])

        assert task["id"] == 1
        assert task["title"] == test_task_data["title"]
        assert task["user_id"] == test_user_db["id"]
        assert task["is_deleted"] is False

    def test_create_task_with_project(self, test_user_db):
        """Test creating task with project assignment."""
        task_data = {
            "title": "Task with Project",
            "description": "Task assigned to project",
            "status": "in_progress",
            "project_id": 1,
        }
        task_in = TaskCreate(**task_data)
        task = create_task_service(task_in, test_user_db["id"])

        assert task["project_id"] == 1

    def test_create_multiple_tasks(self, test_user_db):
        """Test creating multiple tasks increments IDs."""
        task_in1 = TaskCreate(title="Task 1", status="pending")
        task1 = create_task_service(task_in1, test_user_db["id"])

        task_in2 = TaskCreate(title="Task 2", status="in_progress")
        task2 = create_task_service(task_in2, test_user_db["id"])

        assert task1["id"] == 1
        assert task2["id"] == 2
        assert len(fake_tasks_db) == 2

    def test_create_task_default_status(self, test_user_db):
        """Test that task status defaults to pending."""
        task_in = TaskCreate(title="Task without status")
        task = create_task_service(task_in, test_user_db["id"])

        assert task["status"] == "pending"


class TestGetTasksForUser:
    """Tests for retrieving user tasks."""

    def test_get_tasks_for_user_empty(self, test_user_db):
        """Test getting tasks for user with no tasks."""
        tasks = get_tasks_for_user_service(test_user_db["id"])

        assert tasks == []

    def test_get_tasks_for_user_single(self, test_user_db):
        """Test getting single task for user."""
        task_in = TaskCreate(title="Task 1")
        task = create_task_service(task_in, test_user_db["id"])

        tasks = get_tasks_for_user_service(test_user_db["id"])

        assert len(tasks) == 1
        assert tasks[0]["id"] == task["id"]

    def test_get_tasks_for_user_multiple(self, test_user_db):
        """Test getting multiple tasks for user."""
        for i in range(3):
            task_in = TaskCreate(title=f"Task {i+1}")
            create_task_service(task_in, test_user_db["id"])

        tasks = get_tasks_for_user_service(test_user_db["id"])

        assert len(tasks) == 3

    def test_get_tasks_for_user_different_users(self, test_user_db, test_second_user_db):
        """Test that tasks are not mixed between users."""
        # Create tasks for user 1
        for i in range(2):
            task_in = TaskCreate(title=f"User1 Task {i+1}")
            create_task_service(task_in, test_user_db["id"])

        # Create tasks for user 2
        for i in range(3):
            task_in = TaskCreate(title=f"User2 Task {i+1}")
            create_task_service(task_in, test_second_user_db["id"])

        # Get tasks for user 1
        tasks_user1 = get_tasks_for_user_service(test_user_db["id"])
        assert len(tasks_user1) == 2

        # Get tasks for user 2
        tasks_user2 = get_tasks_for_user_service(test_second_user_db["id"])
        assert len(tasks_user2) == 3

    def test_get_tasks_excludes_deleted(self, test_user_db):
        """Test that deleted tasks are not returned."""
        task_in = TaskCreate(title="Task to delete")
        task = create_task_service(task_in, test_user_db["id"])

        # Mark task as deleted
        delete_task_service(task["id"])

        tasks = get_tasks_for_user_service(test_user_db["id"])

        assert len(tasks) == 0


class TestGetTaskById:
    """Tests for retrieving single task."""

    def test_get_task_by_id_success(self, test_user_db):
        """Test retrieving existing task."""
        task_in = TaskCreate(title="Task")
        created_task = create_task_service(task_in, test_user_db["id"])

        task = get_task_by_id_service(created_task["id"])

        assert task is not None
        assert task["id"] == created_task["id"]
        assert task["title"] == "Task"

    def test_get_task_by_id_nonexistent(self):
        """Test retrieving non-existent task."""
        task = get_task_by_id_service(999)

        assert task is None

    def test_get_task_by_id_deleted(self, test_user_db):
        """Test that deleted tasks are not returned."""
        task_in = TaskCreate(title="Task to delete")
        task = create_task_service(task_in, test_user_db["id"])

        delete_task_service(task["id"])

        retrieved = get_task_by_id_service(task["id"])

        assert retrieved is None


class TestUpdateTask:
    """Tests for updating tasks."""

    def test_update_task_title(self, test_user_db):
        """Test updating task title."""
        task_in = TaskCreate(title="Original Title")
        task = create_task_service(task_in, test_user_db["id"])

        update_data = TaskUpdate(title="Updated Title")
        updated = update_task_service(task, update_data)

        assert updated["title"] == "Updated Title"

    def test_update_task_status(self, test_user_db):
        """Test updating task status."""
        task_in = TaskCreate(title="Task", status="pending")
        task = create_task_service(task_in, test_user_db["id"])

        update_data = TaskUpdate(status="completed")
        updated = update_task_service(task, update_data)

        assert updated["status"] == "completed"

    def test_update_task_multiple_fields(self, test_user_db):
        """Test updating multiple fields."""
        task_in = TaskCreate(title="Task", status="pending")
        task = create_task_service(task_in, test_user_db["id"])

        update_data = TaskUpdate(
            title="New Title",
            status="in_progress",
            description="New description"
        )
        updated = update_task_service(task, update_data)

        assert updated["title"] == "New Title"
        assert updated["status"] == "in_progress"
        assert updated["description"] == "New description"

    def test_update_task_partial(self, test_user_db):
        """Test partial update (only one field)."""
        task_in = TaskCreate(title="Task", status="pending",
                             description="Original")
        task = create_task_service(task_in, test_user_db["id"])

        update_data = TaskUpdate(title="New Title")
        updated = update_task_service(task, update_data)

        assert updated["title"] == "New Title"
        assert updated["status"] == "pending"
        assert updated["description"] == "Original"


class TestDeleteTask:
    """Tests for deleting tasks."""

    def test_delete_task_success(self, test_user_db):
        """Test successful task deletion."""
        task_in = TaskCreate(title="Task to delete")
        task = create_task_service(task_in, test_user_db["id"])

        result = delete_task_service(task["id"])

        assert result is True
        # Soft delete: task should be marked as deleted
        assert fake_tasks_db[0]["is_deleted"] is True

    def test_delete_task_nonexistent(self):
        """Test deleting non-existent task."""
        result = delete_task_service(999)

        assert result is False

    def test_delete_task_cannot_retrieve(self, test_user_db):
        """Test that deleted task cannot be retrieved."""
        task_in = TaskCreate(title="Task")
        task = create_task_service(task_in, test_user_db["id"])

        delete_task_service(task["id"])

        retrieved = get_task_by_id_service(task["id"])
        assert retrieved is None

    def test_delete_task_not_in_user_list(self, test_user_db):
        """Test that deleted task is not in user task list."""
        task_in = TaskCreate(title="Task")
        task = create_task_service(task_in, test_user_db["id"])

        delete_task_service(task["id"])

        user_tasks = get_tasks_for_user_service(test_user_db["id"])
        assert len(user_tasks) == 0


class TestFilterTasksByStatus:
    """Tests for filtering tasks by status."""

    def test_filter_tasks_by_status_pending(self, test_user_db):
        """Test filtering pending tasks."""
        # Create tasks with different statuses
        for status in ["pending", "in_progress", "completed", "pending"]:
            task_in = TaskCreate(title=f"Task {status}", status=status)
            create_task_service(task_in, test_user_db["id"])

        tasks = filter_tasks_by_status_service(test_user_db["id"], "pending")

        assert len(tasks) == 2
        assert all(t["status"] == "pending" for t in tasks)

    def test_filter_tasks_by_status_no_matches(self, test_user_db):
        """Test filtering with no matching tasks."""
        task_in = TaskCreate(title="Task", status="pending")
        create_task_service(task_in, test_user_db["id"])

        tasks = filter_tasks_by_status_service(test_user_db["id"], "completed")

        assert len(tasks) == 0

    def test_filter_tasks_excludes_deleted(self, test_user_db):
        """Test that deleted tasks are excluded from filter."""
        task_in = TaskCreate(title="Task", status="pending")
        task = create_task_service(task_in, test_user_db["id"])

        delete_task_service(task["id"])

        tasks = filter_tasks_by_status_service(test_user_db["id"], "pending")

        assert len(tasks) == 0

    def test_filter_tasks_user_isolation(self, test_user_db, test_second_user_db):
        """Test that filter only returns tasks for specific user."""
        # Create tasks for user 1
        for i in range(2):
            task_in = TaskCreate(title=f"Task {i+1}", status="pending")
            create_task_service(task_in, test_user_db["id"])

        # Create completed task for user 2
        task_in = TaskCreate(title="User 2 task", status="completed")
        create_task_service(task_in, test_second_user_db["id"])

        tasks = filter_tasks_by_status_service(test_user_db["id"], "pending")

        assert len(tasks) == 2


class TestSearchTasksByTitle:
    """Tests for searching tasks by title."""

    def test_search_tasks_exact_match(self, test_user_db):
        """Test searching with exact title match."""
        task_in = TaskCreate(title="My Important Task")
        create_task_service(task_in, test_user_db["id"])

        tasks = search_tasks_by_title_service(
            test_user_db["id"], "My Important Task")

        assert len(tasks) == 1
        assert tasks[0]["title"] == "My Important Task"

    def test_search_tasks_partial_match(self, test_user_db):
        """Test searching with partial title match."""
        task_in = TaskCreate(title="Buy groceries")
        create_task_service(task_in, test_user_db["id"])

        tasks = search_tasks_by_title_service(test_user_db["id"], "groc")

        assert len(tasks) == 1

    def test_search_tasks_case_insensitive(self, test_user_db):
        """Test that search is case-insensitive."""
        task_in = TaskCreate(title="Buy Groceries")
        create_task_service(task_in, test_user_db["id"])

        tasks = search_tasks_by_title_service(
            test_user_db["id"], "buy groceries")

        assert len(tasks) == 1

    def test_search_tasks_no_matches(self, test_user_db):
        """Test search with no matching tasks."""
        task_in = TaskCreate(title="Buy groceries")
        create_task_service(task_in, test_user_db["id"])

        tasks = search_tasks_by_title_service(
            test_user_db["id"], "nonexistent")

        assert len(tasks) == 0

    def test_search_tasks_multiple_matches(self, test_user_db):
        """Test search that matches multiple tasks."""
        for title in ["Buy milk", "Buy butter", "Buy eggs"]:
            task_in = TaskCreate(title=title)
            create_task_service(task_in, test_user_db["id"])

        tasks = search_tasks_by_title_service(test_user_db["id"], "Buy")

        assert len(tasks) == 3

    def test_search_tasks_excludes_deleted(self, test_user_db):
        """Test that deleted tasks are excluded from search."""
        task_in = TaskCreate(title="Buy groceries")
        task = create_task_service(task_in, test_user_db["id"])

        delete_task_service(task["id"])

        tasks = search_tasks_by_title_service(test_user_db["id"], "Buy")

        assert len(tasks) == 0
