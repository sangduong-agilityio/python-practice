"""
tests/conftest.py
-----------------
Shared pytest fixtures used across all test files.

pytest fixtures are functions that set up test prerequisites (like a DB
session or an HTTP client) and clean up after each test.

Key fixtures here:
  - `db_session` : A fresh SQLite in-memory DB for each test (fast, no Docker needed).
  - `client`     : An async HTTP client wired to the FastAPI app with the test DB.
  - `test_user`  : A pre-created user for tests that need authentication.
  - `auth_headers`: JWT headers for the test user.
"""

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.dependencies import get_db
from app.core.security import create_access_token
from app.db.session import Base
from app.main import app
from app.models.user import User
from app.core.security import hash_password

# ---------------------------------------------------------------------------
# Test database — SQLite in memory (no external Postgres needed for tests)
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    """
    Create all tables once before the test session starts.
    Drop them after all tests finish.

    `scope="session"` means this runs once for the entire test run,
    not once per test function (which would be slow).
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """
    Provide a clean database session for each test.

    Uses a transaction that is rolled back after each test, so each test
    starts with a clean slate without having to recreate all tables.
    """
    async with TestingSessionLocal() as session:
        yield session
        # Roll back any changes made during the test
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    """
    Provide an async HTTP test client backed by the FastAPI app.

    We override the `get_db` dependency so the app uses our test
    SQLite session instead of the real Postgres connection.
    """

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    # Clean up the override after the test
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """
    Create and return a test user directly in the DB (bypassing the API).

    This is faster than registering via the HTTP endpoint and lets us
    create users in a known state.
    """
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=hash_password("testpassword123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """
    Return HTTP headers with a valid JWT for the test user.

    Usage in tests:
        response = await client.get("/api/v1/users/me", headers=auth_headers)
    """
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}
