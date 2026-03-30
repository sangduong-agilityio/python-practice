"""
Integration tests for task routes.
"""
import pytest


class TestCreateTaskRoute:
    def test_create_task_success(self, client, test_user_db, auth_headers, test_task_data):
        response = client.post("/tasks/", json=test_task_data, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == test_task_data["title"]
        assert data["status"] == test_task_data["status"]

    def test_create_task_without_auth(self, client, test_task_data):
        response = client.post("/tasks/", json=test_task_data)
        assert response.status_code == 401

    def test_create_task_default_status(self, client, test_user_db, auth_headers):
        response = client.post("/tasks/", json={"title": "Task without status"}, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["status"] == "pending"


class TestGetTasksRoute:
    def test_get_tasks_empty(self, client, test_user_db, auth_headers):
        response = client.get("/tasks/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_tasks_multiple(self, client, test_user_db, auth_headers):
        for i in range(3):
            client.post("/tasks/", json={"title": f"Task {i+1}"}, headers=auth_headers)
        response = client.get("/tasks/", headers=auth_headers)
        assert len(response.json()) == 3

    def test_get_tasks_without_auth(self, client):
        response = client.get("/tasks/")
        assert response.status_code == 401

    def test_get_tasks_user_isolation(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        client.post("/tasks/", json={"title": "User 1 Task"}, headers=auth_headers)
        client.post("/tasks/", json={"title": "User 2 Task"}, headers=second_auth_headers)

        assert len(client.get("/tasks/", headers=auth_headers).json()) == 1
        assert len(client.get("/tasks/", headers=second_auth_headers).json()) == 1


class TestFilterTasksByStatusRoute:
    def test_filter_tasks_by_status_pending(self, client, test_user_db, auth_headers):
        for status in ["pending", "in_progress", "completed", "pending"]:
            client.post("/tasks/", json={"title": f"Task {status}", "status": status}, headers=auth_headers)

        response = client.get("/tasks/filter/status?status=pending", headers=auth_headers)
        assert response.status_code == 200
        tasks = response.json()
        assert len(tasks) == 2
        assert all(t["status"] == "pending" for t in tasks)

    def test_filter_tasks_no_matches(self, client, test_user_db, auth_headers):
        client.post("/tasks/", json={"title": "Task", "status": "pending"}, headers=auth_headers)
        response = client.get("/tasks/filter/status?status=completed", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_filter_tasks_invalid_status(self, client, test_user_db, auth_headers):
        response = client.get("/tasks/filter/status?status=invalid_status", headers=auth_headers)
        assert response.status_code == 422


class TestSearchTasksByTitleRoute:
    def test_search_tasks_success(self, client, test_user_db, auth_headers):
        client.post("/tasks/", json={"title": "Buy groceries"}, headers=auth_headers)
        response = client.get("/tasks/search/title?q=groc", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_search_tasks_case_insensitive(self, client, test_user_db, auth_headers):
        client.post("/tasks/", json={"title": "Buy Groceries"}, headers=auth_headers)
        response = client.get("/tasks/search/title?q=buy groceries", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_search_tasks_without_auth(self, client):
        response = client.get("/tasks/search/title?q=test")
        assert response.status_code == 401


class TestGetTaskByIdRoute:
    def test_get_task_by_id_success(self, client, test_user_db, auth_headers):
        task_id = client.post("/tasks/", json={"title": "Task"}, headers=auth_headers).json()["id"]
        response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["id"] == task_id

    def test_get_task_by_id_nonexistent(self, client, test_user_db, auth_headers):
        response = client.get("/tasks/999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_task_by_id_unauthorized(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        task_id = client.post("/tasks/", json={"title": "User 2 Task"}, headers=second_auth_headers).json()["id"]
        response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 403


class TestUpdateTaskRoute:
    def test_update_task_success(self, client, test_user_db, auth_headers):
        task_id = client.post("/tasks/", json={"title": "Original"}, headers=auth_headers).json()["id"]
        response = client.put(f"/tasks/{task_id}", json={"title": "Updated"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["title"] == "Updated"

    def test_update_task_nonexistent(self, client, test_user_db, auth_headers):
        response = client.put("/tasks/999", json={"title": "Updated"}, headers=auth_headers)
        assert response.status_code == 404

    def test_update_task_unauthorized(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        task_id = client.post("/tasks/", json={"title": "User 2 Task"}, headers=second_auth_headers).json()["id"]
        response = client.put(f"/tasks/{task_id}", json={"title": "Updated"}, headers=auth_headers)
        assert response.status_code == 403


class TestDeleteTaskRoute:
    def test_delete_task_success(self, client, test_user_db, auth_headers):
        task_id = client.post("/tasks/", json={"title": "Task to delete"}, headers=auth_headers).json()["id"]
        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 204

        get_response = client.get(f"/tasks/{task_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_task_nonexistent(self, client, test_user_db, auth_headers):
        response = client.delete("/tasks/999", headers=auth_headers)
        assert response.status_code == 404

    def test_delete_task_unauthorized(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        task_id = client.post("/tasks/", json={"title": "User 2 Task"}, headers=second_auth_headers).json()["id"]
        response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
        assert response.status_code == 403
