"""Shared test fixtures for integration tests.

This is the root conftest.py used by all tests (integration and unit).

The test database uses SQLite in-memory so tests run without a live
PostgreSQL instance. Each test gets its own transaction that is rolled
back at the end, keeping tests isolated from each other.

Fixtures provided:
- event_loop: Session-scoped event loop for async tests
- engine: SQLite in-memory database engine (session-scoped)
- db_session: Database session per test (function-scoped)
- client: Async HTTP client with dependency override (function-scoped)

Test data helpers:
- TEST_USER, SECOND_USER: Sample user credentials
- create_user(): Register a user via HTTP endpoint
- get_token(): Login and get JWT access token
- auth_headers(): Get Authorization header with Bearer token
"""

from app.models.base import Base
from app.main import app
from app.core.rate_limit import limiter
from app.core.dependencies import get_db
import asyncio
import os
from types import SimpleNamespace
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key")


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    # A single event loop for the whole test session is required when
    # session-scoped async fixtures share state across tests.
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_redis():
    """Globally mock Redis to avoid real connections in tests.
    This prevents 'Event loop is closed' errors and doesn't require a live Redis.
    """
    mock_client = AsyncMock()
    mock_client.get.return_value = None
    mock_client.exists.return_value = 0
    mock_client.ping.return_value = True

    async def _scan_iter(*, match: str | None = None, count: int | None = None):
        # Yield a deterministic key so cache invalidation calls exercise delete().
        # Tests should not rely on the exact Redis key structure.
        yield "test:key:1"

    # AsyncMock would turn this into a coroutine; we need an async-iterable.
    mock_client.scan_iter = _scan_iter  # type: ignore[assignment]

    with (
        patch("app.core.cache.get_redis_client", return_value=mock_client),
        patch("app.main.get_redis_client", return_value=mock_client),
    ):
        yield mock_client


@pytest.fixture(autouse=True)
def mock_celery_tasks():
    """Mock Celery tasks so tests never touch Redis broker/result backend."""
    fake_result = SimpleNamespace(id="test-task-id")
    with (
        patch("app.services.user_service.send_welcome_email") as welcome,
        patch("app.services.task_service.send_task_assigned_email") as assigned,
    ):
        welcome.delay.return_value = fake_result
        assigned.delay.return_value = fake_result
        yield


@pytest_asyncio.fixture(scope="session")
async def engine():
    test_engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await test_engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    TestSession = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    # Override the real DB dependency with the test session so route
    # handlers operate on the same in-memory database as the test.
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Disable rate limiting during tests to avoid 429 Too Many Requests
    limiter.enabled = False

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
    limiter.enabled = True  # Re-enable for next test session if needed


# ---------------------------------------------------------------------------
# Reusable helpers -- not fixtures themselves, called inside tests or
# other fixtures that need an authenticated user.
# ---------------------------------------------------------------------------

TEST_USER = {
    "email": "alice@example.com",
    "username": "alice",
    "password": "strongpassword1",
}

SECOND_USER = {
    "email": "bob@example.com",
    "username": "bob",
    "password": "strongpassword2",
}


async def create_user(client: AsyncClient, payload: dict = TEST_USER) -> dict:
    """Register a user. Safe to call multiple times (idempotent)."""
    r = await client.post("/api/v1/auth/register", json=payload)
    if r.status_code == 409:
        return payload
    assert r.status_code == 201, r.text
    return r.json()


async def create_user_with_token(client: AsyncClient, payload: dict = TEST_USER) -> tuple[dict, str]:
    """Register and log in a user, returning (user_data, access_token)."""
    user_data = await create_user(client, payload)
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert r.status_code == 200, r.text
    return user_data, r.json()["access_token"]


async def get_token(client: AsyncClient, payload: dict = TEST_USER) -> str:
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": payload["email"], "password": payload["password"]},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


async def auth_headers(client: AsyncClient, payload: dict = TEST_USER) -> dict:
    token = await get_token(client, payload)
    return {"Authorization": f"Bearer {token}"}
