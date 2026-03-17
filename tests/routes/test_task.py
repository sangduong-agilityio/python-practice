"""
Tests for task routes.
"""
import pytest


class TestCreateTaskRoute:
    """Tests for POST /tasks endpoint."""

    def test_create_task_success(self, client, test_user_db, auth_headers, test_task_data):
        """Test successful task creation."""
        response = client.post(
            "/tasks/",
            json=test_task_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["title"] == test_task_data["title"]
        assert data["description"] == test_task_data["description"]
        assert data["status"] == test_task_data["status"]

    def test_create_task_without_auth(self, client, test_task_data):
        """Test task creation without authentication."""
        response = client.post("/tasks/", json=test_task_data)

        assert response.status_code == 401

    def test_create_task_with_project(self, client, test_user_db, auth_headers):
        """Test creating task with project assignment."""
        response = client.post(
            "/tasks/",
            json={"title": "Task", "project_id": 1},
            headers=auth_headers
        )

        assert response.status_code == 201
        assert response.json()["project_id"] == 1

    def test_create_task_default_status(self, client, test_user_db, auth_headers):
        """Test that task status defaults to pending."""
        response = client.post(
            "/tasks/",
            json={"title": "Task without status"},
            headers=auth_headers
        )

        assert response.status_code == 201
        assert response.json()["status"] == "pending"


class TestGetTasksRoute:
    """Tests for GET /tasks endpoint."""

    def test_get_tasks_empty(self, client, test_user_db, auth_headers):
        """Test getting tasks when user has no tasks."""
        response = client.get("/tasks/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_get_tasks_single(self, client, test_user_db, auth_headers, test_task_data):
        """Test getting single task."""
        # Create task
        create_response = client.post(
            "/tasks/",
            json=test_task_data,
            headers=auth_headers
        )
        created_task_id = create_response.json()["id"]

        # Get tasks
        response = client.get("/tasks/", headers=auth_headers)

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert tasks[0]["id"] == created_task_id

    def test_get_tasks_multiple(self, client, test_user_db, auth_headers):
        """Test getting multiple tasks."""
        # Create 3 tasks
        for i in range(3):
            client.post(
                "/tasks/",
                json={"title": f"Task {i+1}"},
                headers=auth_headers
            )

        # Get tasks
        response = client.get("/tasks/", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_get_tasks_without_auth(self, client):
        """Test getting tasks without authentication."""
        response = client.get("/tasks/")

        assert response.status_code == 401

    def test_get_tasks_user_isolation(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        """Test that each user only sees their own tasks."""
        # Create task for user 1
        client.post(
            "/tasks/",
            json={"title": "User 1 Task"},
            headers=auth_headers
        )

        # Create task for user 2
        client.post(
            "/tasks/",
            json={"title": "User 2 Task"},
            headers=second_auth_headers
        )

        # User 1 should only see 1 task
        response1 = client.get("/tasks/", headers=auth_headers)
        assert len(response1.json()) == 1

        # User 2 should only see 1 task
        response2 = client.get("/tasks/", headers=second_auth_headers)
        assert len(response2.json()) == 1


class TestFilterTasksByStatusRoute:
    """Tests for GET /tasks/filter/status endpoint."""

    def test_filter_tasks_by_status_pending(self, client, test_user_db, auth_headers):
        """Test filtering pending tasks."""
        # Create tasks with different statuses
        for status in ["pending", "in_progress", "completed", "pending"]:
            client.post(
                "/tasks/",
                json={"title": f"Task {status}", "status": status},
                headers=auth_headers
            )

        response = client.get(
            "/tasks/filter/status?status=pending",
            headers=auth_headers
        )

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert all(t["status"] == "pending" for t in tasks)

    def test_filter_tasks_no_matches(self, client, test_user_db, auth_headers):
        """Test filter with no matching tasks."""
        client.post(
            "/tasks/",
            json={"title": "Pending task", "status": "pending"},
            headers=auth_headers
        )

        response = client.get(
            "/tasks/filter/status?status=completed",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_filter_tasks_without_auth(self, client):
        """Test filter without authentication."""
        response = client.get("/tasks/filter/status?status=pending")

        assert response.status_code == 401

    def test_filter_tasks_invalid_status(self, client, test_user_db, auth_headers):
        """Test filter with invalid status."""
        response = client.get(
            "/tasks/filter/status?status=invalid_status",
            headers=auth_headers
        )

        # FastAPI should return 422 for invalid enum value
        assert response.status_code == 422


class TestSearchTasksByTitleRoute:
    """Tests for GET /tasks/search/title endpoint."""

    def test_search_tasks_success(self, client, test_user_db, auth_headers):
        """Test successful task search."""
        client.post(
            "/tasks/",
            json={"title": "Buy groceries"},
            headers=auth_headers
        )

        response = client.get(
            "/tasks/search/title?q=groc",
            headers=auth_headers
        )

        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 1
        assert "groc" in tasks[0]["title"].lower()

    def test_search_tasks_no_matches(self, client, test_user_db, auth_headers):
        """Test search with no matches."""
        client.post(
            "/tasks/",
            json={"title": "Buy groceries"},
            headers=auth_headers
        )

        response = client.get(
            "/tasks/search/title?q=nonexistent",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json() == []

    def test_search_tasks_case_insensitive(self, client, test_user_db, auth_headers):
        """Test that search is case-insensitive."""
        client.post(
            "/tasks/",
            json={"title": "Buy Groceries"},
            headers=auth_headers
        )

        response = client.get(
            "/tasks/search/title?q=buy groceries",
            headers=auth_headers
        )

        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_search_tasks_without_auth(self, client):
        """Test search without authentication."""
        response = client.get("/tasks/search/title?q=test")

        assert response.status_code == 401


class TestGetTaskByIdRoute:
    """Tests for GET /tasks/{task_id} endpoint."""

    def test_get_task_by_id_success(self, client, test_user_db, auth_headers):
        """Test getting task by ID."""
        create_response = client.post(
            "/tasks/",
            json={"title": "Task"},
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        response = client.get(f"/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 200
        assert response.json()["id"] == task_id

    def test_get_task_by_id_nonexistent(self, client, test_user_db, auth_headers):
        """Test getting non-existent task."""
        response = client.get("/tasks/999", headers=auth_headers)

        assert response.status_code == 404

    def test_get_task_by_id_unauthorized(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        """Test that user cannot get other user's task."""
        # User 2 creates task
        create_response = client.post(
            "/tasks/",
            json={"title": "User 2 Task"},
            headers=second_auth_headers
        )
        task_id = create_response.json()["id"]

        # User 1 tries to get user 2's task
        response = client.get(f"/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 403


class TestUpdateTaskRoute:
    """Tests for PUT /tasks/{task_id} endpoint."""

    def test_update_task_success(self, client, test_user_db, auth_headers):
        """Test successful task update."""
        create_response = client.post(
            "/tasks/",
            json={"title": "Original title"},
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        response = client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated title"},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["title"] == "Updated title"

    def test_update_task_status(self, client, test_user_db, auth_headers):
        """Test updating task status."""
        create_response = client.post(
            "/tasks/",
            json={"title": "Task", "status": "pending"},
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        response = client.put(
            f"/tasks/{task_id}",
            json={"status": "completed"},
            headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["status"] == "completed"

    def test_update_task_nonexistent(self, client, test_user_db, auth_headers):
        """Test updating non-existent task."""
        response = client.put(
            "/tasks/999",
            json={"title": "Updated"},
            headers=auth_headers
        )

        assert response.status_code == 404

    def test_update_task_unauthorized(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        """Test that user cannot update other user's task."""
        # User 2 creates task
        create_response = client.post(
            "/tasks/",
            json={"title": "User 2 Task"},
            headers=second_auth_headers
        )
        task_id = create_response.json()["id"]

        # User 1 tries to update user 2's task
        response = client.put(
            f"/tasks/{task_id}",
            json={"title": "Updated"},
            headers=auth_headers
        )

        assert response.status_code == 403


class TestDeleteTaskRoute:
    """Tests for DELETE /tasks/{task_id} endpoint."""

    def test_delete_task_success(self, client, test_user_db, auth_headers):
        """Test successful task deletion."""
        create_response = client.post(
            "/tasks/",
            json={"title": "Task to delete"},
            headers=auth_headers
        )
        task_id = create_response.json()["id"]

        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 204

        # Task should not be retrievable
        get_response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_task_nonexistent(self, client, test_user_db, auth_headers):
        """Test deleting non-existent task."""
        response = client.delete("/tasks/999", headers=auth_headers)

        assert response.status_code == 404

    def test_delete_task_unauthorized(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        """Test that user cannot delete other user's task."""
        # User 2 creates task
        create_response = client.post(
            "/tasks/",
            json={"title": "User 2 Task"},
            headers=second_auth_headers
        )
        task_id = create_response.json()["id"]

        # User 1 tries to delete user 2's task
        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)

        assert response.status_code == 403
