"""
Shared fixtures and configuration for all tests.
"""
from src.fastapi_training.app.schemas.user import UserCreate
from src.fastapi_training.app.core.security import (
    hash_password,
    create_access_token,
    create_refresh_token,
)
from src.fastapi_training.app.db.fake_db import fake_users_db, fake_tasks_db, fake_projects_db
from src.fastapi_training.app.main import app
from datetime import timedelta
from fastapi.testclient import TestClient
import pytest


@pytest.fixture(autouse=True)
def clear_db():
    """Clear fake databases before each test."""
    fake_users_db.clear()
    fake_tasks_db.clear()
    fake_projects_db.clear()
    yield
    fake_users_db.clear()
    fake_tasks_db.clear()
    fake_projects_db.clear()


@pytest.fixture
def client():
    """Provide FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
    }


@pytest.fixture
def test_password_invalid():
    """Provide invalid password for testing."""
    return "short"  # Less than 8 characters


@pytest.fixture
def test_user_db(test_user_data):
    """Create a test user in the database."""
    user = {
        "id": 1,
        "email": test_user_data["email"],
        "hashed_password": hash_password(test_user_data["password"]),
    }
    fake_users_db.append(user)
    return user


@pytest.fixture
def test_user_token(test_user_data):
    """Generate access token for test user."""
    return create_access_token(data={"sub": test_user_data["email"]})


@pytest.fixture
def test_user_refresh_token(test_user_data):
    """Generate refresh token for test user."""
    return create_refresh_token(data={"sub": test_user_data["email"]})


@pytest.fixture
def test_user_expired_token(test_user_data):
    """Generate expired access token for testing."""
    from src.fastapi_training.app.core.config import settings
    from jose import jwt
    from datetime import datetime, timezone

    # Create token with past expiration
    to_encode = {"sub": test_user_data["email"]}
    expire = datetime.now(timezone.utc) - timedelta(minutes=1)
    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


@pytest.fixture
def auth_headers(test_user_token):
    """Provide authorization headers with valid token."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def test_second_user_data():
    """Provide second test user data."""
    return {
        "email": "second@example.com",
        "password": "SecondPass123",
    }


@pytest.fixture
def test_second_user_db(test_second_user_data):
    """Create a second test user in the database."""
    user = {
        "id": 2,
        "email": test_second_user_data["email"],
        "hashed_password": hash_password(test_second_user_data["password"]),
    }
    fake_users_db.append(user)
    return user


@pytest.fixture
def test_second_user_token(test_second_user_data):
    """Generate access token for second test user."""
    return create_access_token(data={"sub": test_second_user_data["email"]})


@pytest.fixture
def second_auth_headers(test_second_user_token):
    """Provide authorization headers for second user."""
    return {"Authorization": f"Bearer {test_second_user_token}"}


@pytest.fixture
def test_task_data():
    """Provide test task data."""
    return {
        "title": "Test Task",
        "description": "This is a test task",
        "status": "pending",
        "project_id": None,
    }


@pytest.fixture
def test_project_data():
    """Provide test project data."""
    return {
        "name": "Test Project",
        "description": "This is a test project",
    }
