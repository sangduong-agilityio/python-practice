"""
Test configuration and fixtures for the FastAPI application.

This module provides:
- TestClient setup
- Database isolation for tests
- Test user fixtures
- Authentication fixtures
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.fastapi_training.app.main import app
from src.fastapi_training.app.db.fake_db import fake_users_db, fake_tasks_db, fake_projects_db
from src.fastapi_training.app.core.security import hash_password


@pytest.fixture(autouse=True)
def reset_databases():
    """
    Reset all databases before each test.
    This ensures test isolation.
    """
    fake_users_db.clear()
    fake_tasks_db.clear()
    fake_projects_db.clear() 

    # Add test user
    fake_users_db.append({
        "id": 1,
        "email": "test@example.com",
        "hashed_password": hash_password("password123")
    })

    yield

    # Cleanup after test
    fake_users_db.clear()
    fake_tasks_db.clear()
    fake_projects_db.clear()


@pytest.fixture
def client():
    """
    TestClient for making requests to the FastAPI app.

    Usage:
        def test_something(client):
            response = client.get("/")
            assert response.status_code == 200
    """
    return TestClient(app)


@pytest.fixture
def test_user():
    """
    Default test user credentials.

    Usage:
        def test_login(client, test_user):
            response = client.post(
                "/auth/token",
                data={
                    "username": test_user["email"],
                    "password": test_user["password"]
                }
            )
    """
    return {
        "email": "test@example.com",
        "password": "password123"
    }


@pytest.fixture
def test_user_2():
    """
    Second test user for authorization testing.
    """
    user_email = "testuser2@example.com"
    user_password = "password456"

    # Add second user to database
    fake_users_db.append({
        "id": 2,
        "email": user_email,
        "hashed_password": hash_password(user_password)
    })

    return {
        "email": user_email,
        "password": user_password
    }


@pytest.fixture
def auth_headers(client, test_user):
    """
    Get Authorization header with valid JWT token for test_user.

    Usage:
        def test_protected_route(client, auth_headers):
            response = client.get("/users/me", headers=auth_headers)
            assert response.status_code == 200
    """
    response = client.post(
        "/auth/token",
        data={
            "username": test_user["email"],
            "password": test_user["password"]
        }
    )

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user_2(client, test_user_2):
    """
    Get Authorization header for test_user_2.
    Useful for testing authorization/access control.
    """
    response = client.post(
        "/auth/token",
        data={
            "username": test_user_2["email"],
            "password": test_user_2["password"]
        }
    )

    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def create_test_task(client, auth_headers):
    """
    Factory fixture to create test tasks.

    Usage:
        def test_task_crud(client, create_test_task):
            task = create_test_task("Learn FastAPI", "pending")
            assert task["id"] == 1
    """
    def _create_task(title="Test Task", status="pending", description="Test description"):
        response = client.post(
            "/tasks/",
            json={
                "title": title,
                "description": description,
                "status": status
            },
            headers=auth_headers
        )
        return response.json()

    return _create_task


@pytest.fixture
def create_test_project(client, auth_headers):
    """
    Factory fixture to create test projects.
    """
    def _create_project(name="Test Project", description="Test project description"):
        response = client.post(
            "/projects/",
            json={
                "name": name,
                "description": description
            },
            headers=auth_headers
        )
        return response.json()

    return _create_project
