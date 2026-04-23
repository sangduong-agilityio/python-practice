"""
Integration tests for authentication endpoints.

Covers the full authentication lifecycle:
- Registration (success and failures)
- Login (OAuth2 password flow)
- Token Refresh (Rotation and reuse detection)
- Logout (Token revocation)
- Access control for protected identity endpoints
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.security import hash_token
from app.models.refresh_token import RefreshToken
from app.models.user import User
from tests.conftest import TEST_USER, create_user


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """Check standard registration flow."""
    r = await client.post("/api/v1/auth/register", json=TEST_USER)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == TEST_USER["email"]
    assert body["username"] == TEST_USER["username"]
    # NEVER return the password or hash back to the client
    assert "password" not in body
    assert "hashed_password" not in body

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Ensure duplicate email bounces."""
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/register",
        json={**TEST_USER, "username": "different_user"},
    )
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient) -> None:
    """Ensure duplicate username bounces."""
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/register",
        json={**TEST_USER, "email": "unique@example.com"},
    )
    assert r.status_code == 409

@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    """Pydantic should block tiny passwords."""
    r = await client.post(
        "/api/v1/auth/register",
        json={**TEST_USER, "password": "short"},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Standard login yielding a fresh pair of tokens."""
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]},
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient) -> None:
    """Bad password drops a 403."""
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["email"], "password": "wrongpassword"},
    )
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_inactive_user_login_fails(client: AsyncClient, db_session):
    """Deactivated accounts shouldn't be able to log in even with the right password."""
    from app.core.security import hash_password
    user = User(
        email="inactive@example.com",
        username="inactive",
        hashed_password=hash_password("password123"),
        is_active=False
    )
    db_session.add(user)
    await db_session.commit()

    r = await client.post("/api/v1/auth/login", data={"username": "inactive@example.com", "password": "password123"})
    assert r.status_code == 403
    assert "inactive" in r.json()["detail"].lower()

@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient):
    """Check rotation: passing an old refresh token gives a completely new pair."""
    await create_user(client)

    # login once
    r = await client.post("/api/v1/auth/login", data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    old_refresh = r.json()["refresh_token"]

    # consume the refresh token
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    new_tokens = r.json()
    assert new_tokens["refresh_token"] != old_refresh
    assert "access_token" in new_tokens

@pytest.mark.asyncio
async def test_refresh_token_reuse_detection(client: AsyncClient):
    """If someone uses an already-consumed refresh token, revoke everything."""
    await create_user(client)
    r = await client.post("/api/v1/auth/login", data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    old_refresh = r.json()["refresh_token"]

    # legit refresh
    await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})

    # suspicious replay attack with the consumed token
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 403
    assert "invalid" in r.json()["detail"].lower() or "expired" in r.json()["detail"].lower()

@pytest.mark.asyncio
async def test_logout_and_revocation(client: AsyncClient):
    """Logout should burn the refresh token and blacklist the JWT access token."""
    await create_user(client)
    r = await client.post("/api/v1/auth/login", data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    r = await client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers)
    assert r.status_code == 204

    # fake out the redis cache for testing the blacklist gate
    with patch("app.core.dependencies.is_token_blacklisted", return_value=True):
        r = await client.get("/api/v1/users/me", headers=headers)
        assert r.status_code == 401

@pytest.mark.asyncio
async def test_refresh_expired_token(client: AsyncClient, db_session):
    """Check that tokens that aged out in the db fail cleanly."""
    email = "expired@example.com"
    await create_user(client, {"email": email, "username": "expired_user", "password": "password123"})
    r = await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    refresh_token = r.json()["refresh_token"]

    # manually advance the clock back in the db to make it expired
    from sqlalchemy import select
    token_hash = hash_token(refresh_token)
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    db_token = result.scalar_one()
    db_token.expires_at = datetime.now(UTC) - timedelta(days=1)
    await db_session.commit()

    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 403
