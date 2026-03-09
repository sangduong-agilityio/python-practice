"""
Test Task CRUD & Authorization

Cover:
- CRUD operations (Create, Read, Update, Delete)
- Access control (own tasks vs other users)
- Error cases
"""

import pytest


class TestTaskCreate:
    """Test task creation."""

    def test_create_task_success(self, client, auth_headers):
        """Test successful task creation."""
        response = client.post(
            "/tasks/",
            json={
                "title": "Learn FastAPI",
                "description": "Complete FastAPI tutorial",
                "status": "pending"
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Learn FastAPI"
        assert data["description"] == "Complete FastAPI tutorial"
        assert data["status"] == "pending"
        assert data["id"] == 1

    def test_create_task_without_auth(self, client):
        """Test task creation without authentication fails."""
        response = client.post(
            "/tasks/",
            json={
                "title": "Test Task",
                "status": "pending"
            }
        )

        assert response.status_code == 401

    def test_create_task_missing_title(self, client, auth_headers):
        """Test task creation without title fails."""
        response = client.post(
            "/tasks/",
            json={
                "status": "pending"
            },
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_create_task_with_default_status(self, client, auth_headers):
        """Test task creation with default status."""
        response = client.post(
            "/tasks/",
            json={
                "title": "Task without status"
            },
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "pending"


class TestTaskRead:
    """Test task retrieval operations."""

    def test_get_all_tasks_empty(self, client, auth_headers):
        """Test getting tasks when none exist."""
        response = client.get(
            "/tasks/",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_get_all_tasks(self, client, auth_headers, create_test_task):
        """Test getting all tasks for current user."""
        # Create 2 tasks
        create_test_task("Task 1", "pending")
        create_test_task("Task 2", "in_progress")

        response = client.get(
            "/tasks/",
            headers=auth_headers
        )

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert tasks[0]["title"] == "Task 1"
        assert tasks[1]["title"] == "Task 2"

    def test_get_task_by_id_success(self, client, auth_headers, create_test_task):
        """Test getting a specific task by ID."""
        create_test_task("Important Task", "in_progress")

        response = client.get(
            "/tasks/1",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Important Task"
        assert data["status"] == "in_progress"

    def test_get_task_not_found(self, client, auth_headers):
        """Test getting non-existent task."""
        response = client.get(
            "/tasks/999",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_get_task_other_user(self, client, auth_headers, auth_headers_user_2, create_test_task):
        """Test accessing other user's task - 403 Forbidden."""
        # User 1 creates task
        create_test_task("User 1 Task")

        # User 2 tries to access it
        response = client.get(
            "/tasks/1",
            headers=auth_headers_user_2
        )

        assert response.status_code == 403
        assert "Not allowed" in response.json()["detail"]


class TestTaskUpdate:
    """Test task update operations."""

    def test_update_task_success(self, client, auth_headers, create_test_task):
        """Test successful task update."""
        create_test_task("Original Title", "pending")

        response = client.put(
            "/tasks/1",
            json={
                "title": "Updated Title",
                "status": "in_progress"
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "in_progress"

    def test_update_task_partial(self, client, auth_headers, create_test_task):
        """Test partial task update."""
        create_test_task("Original", "pending", "Original description")

        response = client.put(
            "/tasks/1",
            json={
                "status": "completed"
                # Only status, keep title
            },
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Original"
        assert data["status"] == "completed"

    def test_update_task_not_found(self, client, auth_headers):
        """Test updating non-existent task."""
        response = client.put(
            "/tasks/999",
            json={"title": "Updated"},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_other_user_task(self, client, auth_headers, auth_headers_user_2, create_test_task):
        """Test other user cannot update task."""
        create_test_task("User 1 Task")

        response = client.put(
            "/tasks/1",
            json={"title": "Hacked Title"},
            headers=auth_headers_user_2
        )

        assert response.status_code == 403


class TestTaskDelete:
    """Test task deletion."""

    def test_delete_task_success(self, client, auth_headers, create_test_task):
        """Test successful task deletion."""
        create_test_task("Task to Delete")

        response = client.delete(
            "/tasks/1",
            headers=auth_headers
        )

        assert response.status_code == 204

        # Verify task is deleted
        get_response = client.get(
            "/tasks/1",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_task_not_found(self, client, auth_headers):
        """Test deleting non-existent task fails."""
        response = client.delete(
            "/tasks/999",
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_delete_other_user_task(self, client, auth_headers, auth_headers_user_2, create_test_task):
        """Test other user cannot delete task."""
        create_test_task("User 1 Task")

        response = client.delete(
            "/tasks/1",
            headers=auth_headers_user_2
        )

        assert response.status_code == 403


class TestTaskFiltering:
    """Test task filtering and searching."""

    def test_filter_by_status(self, client, auth_headers, create_test_task):
        """Test filtering tasks by status."""
        create_test_task("Task 1", "pending")
        create_test_task("Task 2", "in_progress")
        create_test_task("Task 3", "pending")

        response = client.get(
            "/tasks/filter/status?status=pending",
            headers=auth_headers
        )

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert all(task["status"] == "pending" for task in tasks)

    def test_filter_by_invalid_status(self, client, auth_headers):
        """Test filtering with invalid status fails."""
        response = client.get(
            "/tasks/filter/status?status=invalid_status",
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_search_by_title_case_insensitive(self, client, auth_headers, create_test_task):
        """Test case-insensitive title search."""
        create_test_task("Learn FastAPI", "pending")
        create_test_task("Python Basics", "pending")

        # Search lowercase
        response_lower = client.get(
            "/tasks/search/title?q=fastapi",
            headers=auth_headers
        )

        # Search uppercase
        response_upper = client.get(
            "/tasks/search/title?q=FASTAPI",
            headers=auth_headers
        )

        assert response_lower.status_code == 200
        assert response_upper.status_code == 200
        assert len(response_lower.json()) == 1
        assert len(response_upper.json()) == 1
        assert response_lower.json() == response_upper.json()

    def test_search_by_title_partial_match(self, client, auth_headers, create_test_task):
        """Test partial title search."""
        create_test_task("Learn FastAPI", "pending")
        create_test_task("FastAPI Documentation", "pending")
        create_test_task("Python Basics", "pending")

        response = client.get(
            "/tasks/search/title?q=api",
            headers=auth_headers
        )

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert all("API" in task["title"]
                   or "api" in task["title"] for task in tasks)


class TestTaskAuthorization:
    """Test task authorization and data isolation."""

    def test_tasks_isolated_by_user(self, client, auth_headers, auth_headers_user_2, create_test_task):
        """Test that users can only see their own tasks."""
        # User 1 creates tasks
        create_test_task("User 1 Task 1")
        create_test_task("User 1 Task 2")

        # User 1 should see 2 tasks
        user1_tasks = client.get(
            "/tasks/",
            headers=auth_headers
        )
        assert len(user1_tasks.json()) == 2

        # User 2 should see 0 tasks
        user2_tasks = client.get(
            "/tasks/",
            headers=auth_headers_user_2
        )
        assert len(user2_tasks.json()) == 0

    def test_cannot_view_other_user_task(self, client, auth_headers, auth_headers_user_2, create_test_task):
        """Test cannot view other user's task."""
        create_test_task("Secret Task")

        response = client.get(
            "/tasks/1",
            headers=auth_headers_user_2
        )

        assert response.status_code == 403

    def test_cannot_modify_other_user_task(self, client, auth_headers, auth_headers_user_2, create_test_task):
        """Test cannot modify other user's task."""
        create_test_task("Task")

        response = client.put(
            "/tasks/1",
            json={"title": "Hacked"},
            headers=auth_headers_user_2
        )

        assert response.status_code == 403


class TestTaskErrorCases:
    """Test error handling for edge cases."""

    def test_create_task_invalid_status(self, client, auth_headers):
        """Test creating task with invalid status."""
        response = client.post(
            "/tasks/",
            json={
                "title": "Test",
                "status": "invalid_status"
            },
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_get_tasks_without_auth(self, client):
        """Test getting tasks without auth token."""
        response = client.get("/tasks/")

        assert response.status_code == 401

    def test_update_task_invalid_status(self, client, auth_headers, create_test_task):
        """Test updating with invalid status."""
        create_test_task("Task")

        response = client.put(
            "/tasks/1",
            json={"status": "unknown"},
            headers=auth_headers
        )

        assert response.status_code == 422
