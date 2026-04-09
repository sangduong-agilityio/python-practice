"""
Auth endpoint tests.

Each test function covers exactly one behaviour. The test name describes
the scenario so a failing test immediately tells you what broke.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import TEST_USER, auth_headers, create_user


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    r = await client.post("/api/v1/auth/register", json=TEST_USER)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == TEST_USER["email"]
    assert body["username"] == TEST_USER["username"]
    # Password must never appear in any response.
    assert "password" not in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/register",
        json={**TEST_USER, "username": "different"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient) -> None:
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/register",
        json={**TEST_USER, "email": "other@example.com"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/register",
        json={**TEST_USER, "password": "short"},
    )
    # Pydantic rejects it before it reaches the service layer.
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["email"], "password": "wrongpassword"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": "nobody@example.com", "password": "whatever"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient) -> None:
    await create_user(client)
    headers = await auth_headers(client)
    r = await client.get("/api/v1/users/me", headers=headers)
    assert r.status_code == 200
    assert r.json()["email"] == TEST_USER["email"]


@pytest.mark.asyncio
async def test_get_me_unauthenticated(client: AsyncClient) -> None:
    r = await client.get("/api/v1/users/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token(client: AsyncClient) -> None:
    r = await client.get("/api/v1/users/me", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401
