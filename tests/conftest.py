"""
Shared fixtures and configuration for all tests.
Uses async in-memory SQLite DB with SQLModel for isolation.
Each test gets a fresh DB via TestClient with dependency override.
"""
import asyncio
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from src.fastapi_training.main import app
from src.fastapi_training.api.deps import get_db
from src.fastapi_training.core.security import create_access_token
from datetime import timedelta

from src.fastapi_training.models.user import User 
from src.fastapi_training.models.project import Project 
from src.fastapi_training.models.task import Task 
from src.fastapi_training.models.refresh_token import RefreshToken 

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
def client() -> Generator:
    """
    Provide FastAPI TestClient backed by an isolated in-memory SQLite DB.
    DB is created fresh for each test and torn down afterward.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    # Create all tables synchronously before the test
    async def _create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    asyncio.get_event_loop().run_until_complete(_create_tables())

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app, base_url="http://testserver/api/v1") as c:
        yield c

    # Teardown
    async def _drop_tables():
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.drop_all)
        await engine.dispose()

    asyncio.get_event_loop().run_until_complete(_drop_tables())
    app.dependency_overrides.clear()


# --- User Data Fixtures ---

@pytest.fixture
def test_user_data():
    """Provide test user data."""
    return {
        "email": "test@example.com",
        "password": "TestPassword123",
    }


@pytest.fixture
def test_second_user_data():
    """Provide second test user data."""
    return {
        "email": "second@example.com",
        "password": "SecondPass123",
    }


@pytest.fixture
def test_user_db(client, test_user_data):
    """Register a test user via the API and return user dict."""
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 201, f"Registration failed: {response.json()}"
    return response.json()


@pytest.fixture
def test_second_user_db(client, test_second_user_data):
    """Register a second test user via the API and return user dict."""
    response = client.post("/auth/register", json=test_second_user_data)
    assert response.status_code == 201, f"Registration failed: {response.json()}"
    return response.json()


@pytest.fixture
def test_user_token(test_user_data):
    """Generate access token for test user (without DB lookup)."""
    return create_access_token(data={"sub": test_user_data["email"]})


@pytest.fixture
def test_second_user_token(test_second_user_data):
    """Generate access token for second test user."""
    return create_access_token(data={"sub": test_second_user_data["email"]})


@pytest.fixture
def test_user_refresh_token(client, test_user_db, test_user_data):
    """
    Obtain a refresh token via the login API so it is persisted in the DB.
    This is required because the /refresh endpoint now validates tokens against DB.
    """
    response = client.post(
        "/auth/login",
        data={"username": test_user_data["email"], "password": test_user_data["password"]},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    return response.json()["refresh_token"]


@pytest.fixture
def test_user_expired_token(test_user_data):
    """Generate an expired token for test user."""
    return create_access_token(
        data={"sub": test_user_data["email"]},
        expires_delta=timedelta(minutes=-10)
    )


@pytest.fixture
def auth_headers(test_user_db, test_user_token):
    """Provide authorization headers with valid token. Depends on test_user_db to ensure user exists in DB."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def second_auth_headers(test_second_user_db, test_second_user_token):
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
