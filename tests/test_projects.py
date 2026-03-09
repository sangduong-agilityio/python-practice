"""
Tests for Project Management endpoints.

Coverage:
- Create project (authenticated user should get 201)
- Get projects (only show user's projects)
- Assign task to project (authorization checks)
"""

import pytest
from fastapi import status


class TestCreateProject:
    """Test project creation."""

    def test_create_project_success(self, client, auth_headers):
        """
        User can create a project.

        Expected: 201 Created with project data
        """
        response = client.post(
            "/projects/",
            json={
                "name": "My Project",
                "description": "A cool project"
            },
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["id"] == 1
        assert data["name"] == "My Project"
        assert data["description"] == "A cool project"
        assert data["user_id"] == 1

    def test_create_project_minimal(self, client, auth_headers):
        """
        Project can be created with only name (description optional).

        Expected: 201 Created
        """
        response = client.post(
            "/projects/",
            json={"name": "Simple Project"},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Simple Project"
        assert data["description"] is None

    def test_create_project_unauthorized(self, client):
        """
        Anonymous user cannot create project.

        Expected: 401 Unauthorized
        """
        response = client.post(
            "/projects/",
            json={
                "name": "Unauthorized Project",
                "description": "Should fail"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_project_missing_name(self, client, auth_headers):
        """
        Project name is required.

        Expected: 422 Unprocessable Entity (validation error)
        """
        response = client.post(
            "/projects/",
            json={"description": "No name"},
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestGetProjects:
    """Test getting user's projects."""

    def test_get_projects_empty(self, client, auth_headers):
        """
        New user has no projects.

        Expected: 200 OK with empty list
        """
        response = client.get(
            "/projects/",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_get_projects_single(self, client, auth_headers, create_test_project):
        """
        User can get their created projects.

        Expected: 200 OK with list containing the project
        """
        # Create one project
        create_test_project("Project 1")

        response = client.get(
            "/projects/",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        projects = response.json()
        assert len(projects) == 1
        assert projects[0]["name"] == "Project 1"

    def test_get_projects_multiple(self, client, auth_headers, create_test_project):
        """
        User can get multiple projects.

        Expected: 200 OK with all user's projects
        """
        # Create multiple projects
        create_test_project("Project 1")
        create_test_project("Project 2")
        create_test_project("Project 3")

        response = client.get(
            "/projects/",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        projects = response.json()
        assert len(projects) == 3
        names = [p["name"] for p in projects]
        assert "Project 1" in names
        assert "Project 2" in names
        assert "Project 3" in names

    def test_get_projects_other_user_excluded(self, client, auth_headers, auth_headers_user_2, create_test_project):
        """
        User only sees their own projects, not other users' projects.

        Expected: 200 OK with only user's projects
        """
        # User 1 creates a project
        create_test_project("User1 Project")

        # User 2 creates their own project
        # (We need to get user 2's headers and create with them)
        response2 = client.post(
            "/projects/",
            json={"name": "User2 Project"},
            headers=auth_headers_user_2
        )
        assert response2.status_code == status.HTTP_201_CREATED

        # User 1 gets projects - should only see their own
        response = client.get(
            "/projects/",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        projects = response.json()
        assert len(projects) == 1
        assert projects[0]["name"] == "User1 Project"

    def test_get_projects_unauthorized(self, client):
        """
        Anonymous user cannot get projects.

        Expected: 401 Unauthorized
        """
        response = client.get("/projects/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAssignTaskToProject:
    """Test assigning tasks to projects."""

    def test_assign_task_to_project_success(self, client, auth_headers, create_test_task, create_test_project):
        """
        User can assign their task to their project.

        Expected: 200 OK with updated task
        """
        # Create project and task
        project = create_test_project("My Project")
        task = create_test_task("My Task")

        # Assign task to project
        response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == task["id"]
        assert data["project_id"] == project["id"]

    def test_assign_task_project_not_found(self, client, auth_headers, create_test_task):
        """
        Cannot assign task to non-existent project.

        Expected: 404 Not Found
        """
        task = create_test_task("My Task")

        response = client.post(
            f"/projects/999/tasks/{task['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Project not found" in response.json()["detail"]

    def test_assign_task_not_found(self, client, auth_headers, create_test_project):
        """
        Cannot assign non-existent task to project.

        Expected: 404 Not Found
        """
        project = create_test_project("My Project")

        response = client.post(
            f"/projects/{project['id']}/tasks/999",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Task not found" in response.json()["detail"]

    def test_assign_task_project_not_owner(self, client, auth_headers, auth_headers_user_2, create_test_project):
        """
        User cannot assign task to project they don't own.

        Expected: 403 Forbidden
        """
        # User 2 creates a project
        response = client.post(
            "/projects/",
            json={"name": "User2 Project"},
            headers=auth_headers_user_2
        )
        project = response.json()

        # User 1 tries to create task (but this will be user 1's task)
        # So we need to fix this test - let me try another approach
        # Actually, let me create a task with user 1
        response = client.post(
            "/tasks/",
            json={"title": "User1 Task"},
            headers=auth_headers
        )
        task = response.json()

        # User 1 tries to assign their task to User 2's project
        response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not allowed to assign to this project" in response.json()[
            "detail"]

    def test_assign_task_task_not_owner(self, client, auth_headers, auth_headers_user_2, create_test_project):
        """
        User cannot assign task they don't own to their project.

        Expected: 403 Forbidden
        """
        # User 1 creates a project
        project = create_test_project("User1 Project")

        # User 2 creates a task
        response = client.post(
            "/tasks/",
            json={"title": "User2 Task"},
            headers=auth_headers_user_2
        )
        task = response.json()

        # User 1 tries to assign User 2's task to their project
        response = client.post(
            f"/projects/{project['id']}/tasks/{task['id']}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Not allowed to assign this task" in response.json()["detail"]

    def test_assign_task_unauthorized(self, client, create_test_project, create_test_task):
        """
        Anonymous user cannot assign task to project.

        Expected: 401 Unauthorized
        """
        # Use local create_test_project/task would need auth, so we need to set up manually
        # This is tricky, let me skip this for now or handle it differently
        # Actually, the fixtures require auth_headers, so we can't call them without auth
        # Let's just test that the endpoint requires auth

        response = client.post(
            "/projects/1/tasks/1"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_assign_multiple_tasks_to_project(self, client, auth_headers, create_test_task, create_test_project):
        """
        User can assign multiple tasks to the same project.

        Expected: 200 OK for each assignment
        """
        project = create_test_project("My Project")
        task1 = create_test_task("Task 1")
        task2 = create_test_task("Task 2")

        # Assign both tasks
        response1 = client.post(
            f"/projects/{project['id']}/tasks/{task1['id']}",
            headers=auth_headers
        )
        response2 = client.post(
            f"/projects/{project['id']}/tasks/{task2['id']}",
            headers=auth_headers
        )

        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK
        assert response1.json()["project_id"] == project["id"]
        assert response2.json()["project_id"] == project["id"]

    def test_reassign_task_to_different_project(self, client, auth_headers, create_test_task, create_test_project):
        """
        User can reassign a task from one project to another.

        Expected: 200 OK with updated project_id
        """
        project1 = create_test_project("Project 1")
        project2 = create_test_project("Project 2")
        task = create_test_task("My Task")

        # Assign to project 1
        response1 = client.post(
            f"/projects/{project1['id']}/tasks/{task['id']}",
            headers=auth_headers
        )
        assert response1.status_code == 200
        assert response1.json()["project_id"] == project1["id"]

        # Reassign to project 2
        response2 = client.post(
            f"/projects/{project2['id']}/tasks/{task['id']}",
            headers=auth_headers
        )
        assert response2.status_code == 200
        assert response2.json()["project_id"] == project2["id"]
