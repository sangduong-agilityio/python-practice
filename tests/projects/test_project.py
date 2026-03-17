"""
Tests for project routes.
"""
import pytest


class TestCreateProjectRoute:
    """Tests for POST /projects endpoint."""

    def test_create_project_success(self, client, test_user_db, auth_headers, test_project_data):
        """Test successful project creation."""
        response = client.post(
            "/projects/",
            json=test_project_data,
            headers=auth_headers
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_project_data["name"]
        assert data["description"] == test_project_data["description"]
        assert data["tasks"] == []

    def test_create_project_without_auth(self, client, test_project_data):
        """Test project creation without authentication."""
        response = client.post("/projects/", json=test_project_data)

        assert response.status_code == 401

    def test_create_project_without_description(self, client, test_user_db, auth_headers):
        """Test creating project without description."""
        response = client.post(
            "/projects/",
            json={"name": "Project"},
            headers=auth_headers
        )

        assert response.status_code == 201
        assert response.json()["description"] is None


class TestGetProjectsRoute:
    """Tests for GET /projects endpoint."""

    def test_get_projects_empty(self, client, test_user_db, auth_headers):
        """Test getting projects when user has no projects."""
        response = client.get("/projects/", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []

    def test_get_projects_single(self, client, test_user_db, auth_headers, test_project_data):
        """Test getting single project."""
        # Create project
        create_response = client.post(
            "/projects/",
            json=test_project_data,
            headers=auth_headers
        )
        created_project_id = create_response.json()["id"]

        # Get projects
        response = client.get("/projects/", headers=auth_headers)

        assert response.status_code == 200
        projects = response.json()
        assert len(projects) == 1
        assert projects[0]["id"] == created_project_id

    def test_get_projects_multiple(self, client, test_user_db, auth_headers):
        """Test getting multiple projects."""
        # Create 3 projects
        for i in range(3):
            client.post(
                "/projects/",
                json={"name": f"Project {i+1}"},
                headers=auth_headers
            )

        # Get projects
        response = client.get("/projects/", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_get_projects_without_auth(self, client):
        """Test getting projects without authentication."""
        response = client.get("/projects/")

        assert response.status_code == 401

    def test_get_projects_user_isolation(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        """Test that each user only sees their own projects."""
        # Create project for user 1
        client.post(
            "/projects/",
            json={"name": "User 1 Project"},
            headers=auth_headers
        )

        # Create project for user 2
        client.post(
            "/projects/",
            json={"name": "User 2 Project"},
            headers=second_auth_headers
        )

        # User 1 should only see 1 project
        response1 = client.get("/projects/", headers=auth_headers)
        assert len(response1.json()) == 1

        # User 2 should only see 1 project
        response2 = client.get("/projects/", headers=second_auth_headers)
        assert len(response2.json()) == 1

    def test_get_projects_with_tasks(self, client, test_user_db, auth_headers):
        """Test that projects are returned with populated tasks."""
        # Create project
        project_response = client.post(
            "/projects/",
            json={"name": "Project with Tasks"},
            headers=auth_headers
        )
        project_id = project_response.json()["id"]

        # Create and assign task
        task_response = client.post(
            "/tasks/",
            json={"title": "Task 1"},
            headers=auth_headers
        )
        task_id = task_response.json()["id"]

        client.post(
            f"/projects/{project_id}/tasks/{task_id}",
            headers=auth_headers
        )

        # Get projects
        response = client.get("/projects/", headers=auth_headers)

        projects = response.json()
        assert len(projects[0]["tasks"]) == 1
        assert projects[0]["tasks"][0]["id"] == task_id


class TestAssignTaskToProjectRoute:
    """Tests for POST /projects/{project_id}/tasks/{task_id} endpoint."""

    def test_assign_task_to_project_success(self, client, test_user_db, auth_headers):
        """Test successful task assignment."""
        # Create project
        project_response = client.post(
            "/projects/",
            json={"name": "Project"},
            headers=auth_headers
        )
        project_id = project_response.json()["id"]

        # Create task
        task_response = client.post(
            "/tasks/",
            json={"title": "Task"},
            headers=auth_headers
        )
        task_id = task_response.json()["id"]

        # Assign task to project
        response = client.post(
            f"/projects/{project_id}/tasks/{task_id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["project_id"] == project_id

    def test_assign_task_nonexistent_project(self, client, test_user_db, auth_headers):
        """Test assigning task to non-existent project."""
        # Create task
        task_response = client.post(
            "/tasks/",
            json={"title": "Task"},
            headers=auth_headers
        )
        task_id = task_response.json()["id"]

        # Try to assign to non-existent project
        response = client.post(
            f"/projects/999/tasks/{task_id}",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "Project not found" in response.json()["detail"]

    def test_assign_nonexistent_task_to_project(self, client, test_user_db, auth_headers):
        """Test assigning non-existent task to project."""
        # Create project
        project_response = client.post(
            "/projects/",
            json={"name": "Project"},
            headers=auth_headers
        )
        project_id = project_response.json()["id"]

        # Try to assign non-existent task
        response = client.post(
            f"/projects/{project_id}/tasks/999",
            headers=auth_headers
        )

        assert response.status_code == 404
        assert "Task not found" in response.json()["detail"]

    def test_assign_other_user_task_to_own_project(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        """Test that user cannot assign other user's task to own project."""
        # User 1 creates project
        project_response = client.post(
            "/projects/",
            json={"name": "Project"},
            headers=auth_headers
        )
        project_id = project_response.json()["id"]

        # User 2 creates task
        task_response = client.post(
            "/tasks/",
            json={"title": "Task"},
            headers=second_auth_headers
        )
        task_id = task_response.json()["id"]

        # User 1 tries to assign user 2's task to own project
        response = client.post(
            f"/projects/{project_id}/tasks/{task_id}",
            headers=auth_headers
        )

        assert response.status_code == 403
        assert "Not allowed to assign this task" in response.json()["detail"]

    def test_assign_own_task_to_other_user_project(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        """Test that user cannot assign task to other user's project."""
        # User 1 creates project
        project_response = client.post(
            "/projects/",
            json={"name": "Project"},
            headers=auth_headers
        )
        project_id = project_response.json()["id"]

        # User 2 creates task
        task_response = client.post(
            "/tasks/",
            json={"title": "Task"},
            headers=second_auth_headers
        )
        task_id = task_response.json()["id"]

        # Try to assign user 2's task to user 1's project as user 2
        response = client.post(
            f"/projects/{project_id}/tasks/{task_id}",
            headers=second_auth_headers
        )

        assert response.status_code == 403
        assert "Not allowed to assign to this project" in response.json()[
            "detail"]

    def test_assign_task_without_auth(self, client):
        """Test task assignment without authentication."""
        response = client.post("/projects/1/tasks/1")

        assert response.status_code == 401

    def test_assign_same_task_twice(self, client, test_user_db, auth_headers):
        """Test assigning same task to project twice."""
        # Create project
        project_response = client.post(
            "/projects/",
            json={"name": "Project"},
            headers=auth_headers
        )
        project_id = project_response.json()["id"]

        # Create task
        task_response = client.post(
            "/tasks/",
            json={"title": "Task"},
            headers=auth_headers
        )
        task_id = task_response.json()["id"]

        # Assign task twice
        response1 = client.post(
            f"/projects/{project_id}/tasks/{task_id}",
            headers=auth_headers
        )
        assert response1.status_code == 200

        response2 = client.post(
            f"/projects/{project_id}/tasks/{task_id}",
            headers=auth_headers
        )
        assert response2.status_code == 200

        # Verify task is only in project once
        get_response = client.get("/projects/", headers=auth_headers)
        tasks = get_response.json()[0]["tasks"]
        # Count how many times task_id appears
        count = sum(1 for task in tasks if task["id"] == task_id)
        assert count == 1

    def test_assign_multiple_tasks_to_project(self, client, test_user_db, auth_headers):
        """Test assigning multiple tasks to same project."""
        # Create project
        project_response = client.post(
            "/projects/",
            json={"name": "Project"},
            headers=auth_headers
        )
        project_id = project_response.json()["id"]

        # Create and assign multiple tasks
        for i in range(3):
            task_response = client.post(
                "/tasks/",
                json={"title": f"Task {i+1}"},
                headers=auth_headers
            )
            task_id = task_response.json()["id"]

            response = client.post(
                f"/projects/{project_id}/tasks/{task_id}",
                headers=auth_headers
            )
            assert response.status_code == 200

        # Verify all tasks are in project
        get_response = client.get("/projects/", headers=auth_headers)
        tasks = get_response.json()[0]["tasks"]
        assert len(tasks) == 3
