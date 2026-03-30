"""
Integration tests for project routes.
"""
import pytest


class TestCreateProjectRoute:
    def test_create_project_success(self, client, test_user_db, auth_headers, test_project_data):
        response = client.post("/projects/", json=test_project_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == test_project_data["name"]
        assert data["tasks"] == []

    def test_create_project_without_auth(self, client, test_project_data):
        response = client.post("/projects/", json=test_project_data)
        assert response.status_code == 401

    def test_create_project_without_description(self, client, test_user_db, auth_headers):
        response = client.post("/projects/", json={"name": "Project"}, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["description"] is None


class TestGetProjectsRoute:
    def test_get_projects_empty(self, client, test_user_db, auth_headers):
        response = client.get("/projects/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_projects_multiple(self, client, test_user_db, auth_headers):
        for i in range(3):
            client.post("/projects/", json={"name": f"Project {i+1}"}, headers=auth_headers)
        response = client.get("/projects/", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 3

    def test_get_projects_without_auth(self, client):
        response = client.get("/projects/")
        assert response.status_code == 401

    def test_get_projects_user_isolation(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        client.post("/projects/", json={"name": "User 1 Project"}, headers=auth_headers)
        client.post("/projects/", json={"name": "User 2 Project"}, headers=second_auth_headers)

        assert len(client.get("/projects/", headers=auth_headers).json()) == 1
        assert len(client.get("/projects/", headers=second_auth_headers).json()) == 1

    def test_get_projects_with_tasks(self, client, test_user_db, auth_headers):
        project_id = client.post("/projects/", json={"name": "Project"}, headers=auth_headers).json()["id"]
        task_id = client.post("/tasks/", json={"title": "Task 1"}, headers=auth_headers).json()["id"]
        client.post(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)

        response = client.get("/projects/", headers=auth_headers)
        assert len(response.json()[0]["tasks"]) == 1


class TestAssignTaskToProjectRoute:
    def test_assign_task_to_project_success(self, client, test_user_db, auth_headers):
        project_id = client.post("/projects/", json={"name": "Project"}, headers=auth_headers).json()["id"]
        task_id = client.post("/tasks/", json={"title": "Task"}, headers=auth_headers).json()["id"]

        response = client.post(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["project_id"] == project_id

    def test_assign_task_nonexistent_project(self, client, test_user_db, auth_headers):
        task_id = client.post("/tasks/", json={"title": "Task"}, headers=auth_headers).json()["id"]
        response = client.post(f"/projects/999/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_assign_nonexistent_task_to_project(self, client, test_user_db, auth_headers):
        project_id = client.post("/projects/", json={"name": "Project"}, headers=auth_headers).json()["id"]
        response = client.post(f"/projects/{project_id}/tasks/999", headers=auth_headers)
        assert response.status_code == 404

    def test_assign_other_user_task_to_own_project(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        project_id = client.post("/projects/", json={"name": "Project"}, headers=auth_headers).json()["id"]
        task_id = client.post("/tasks/", json={"title": "Task"}, headers=second_auth_headers).json()["id"]

        response = client.post(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 403
        assert "Not allowed to assign this task" in response.json()["detail"]

    def test_assign_task_without_auth(self, client):
        response = client.post("/projects/1/tasks/1")
        assert response.status_code == 401

    def test_assign_multiple_tasks_to_project(self, client, test_user_db, auth_headers):
        project_id = client.post("/projects/", json={"name": "Project"}, headers=auth_headers).json()["id"]
        for i in range(3):
            task_id = client.post("/tasks/", json={"title": f"Task {i+1}"}, headers=auth_headers).json()["id"]
            client.post(f"/projects/{project_id}/tasks/{task_id}", headers=auth_headers)

        tasks = client.get("/projects/", headers=auth_headers).json()[0]["tasks"]
        assert len(tasks) == 3
