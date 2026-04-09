"""
Shared test fixtures.

The test database uses SQLite in-memory so tests run without a live
PostgreSQL instance. Each test gets its own transaction that is rolled
back at the end, keeping tests isolated from each other.
"""

import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.dependencies import get_db
from app.main import app
from app.models.base import Base

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    # A single event loop for the whole test session is required when
    # session-scoped async fixtures share state across tests.
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


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
async def db_session(engine) -> AsyncSession:
    TestSession = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    # Override the real DB dependency with the test session so route
    # handlers operate on the same in-memory database as the test.
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


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
    r = await client.post("/api/v1/auth/register", json=payload)
    assert r.status_code == 201, r.text
    return r.json()


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
