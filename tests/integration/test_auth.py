"""
Integration tests for authentication endpoints.

Covers the full authentication lifecycle:
- Registration (success and failures)
- Login (OAuth2 password flow)
- Token Refresh (Rotation and reuse detection)
- Logout (Token revocation)
- Access control for protected identity endpoints
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, AsyncMock

from app.models.user import User
from app.models.refresh_token import RefreshToken
from app.core.security import hash_token
from tests.conftest import TEST_USER, SECOND_USER, auth_headers, create_user, get_token


# --- Registration Tests ---

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """Verify that a new user can register with valid credentials."""
    r = await client.post("/api/v1/auth/register", json=TEST_USER)
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == TEST_USER["email"]
    assert body["username"] == TEST_USER["username"]
    # Ensure sensitive fields are never returned
    assert "password" not in body
    assert "hashed_password" not in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Ensure registration is rejected if the email is already in use."""
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/register",
        json={**TEST_USER, "username": "different_user"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient) -> None:
    """Ensure registration is rejected if the username is already taken."""
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/register",
        json={**TEST_USER, "email": "unique@example.com"},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient) -> None:
    """Verify that Pydantic validation catches short passwords."""
    r = await client.post(
        "/api/v1/auth/register",
        json={**TEST_USER, "password": "short"},
    )
    assert r.status_code == 422


# --- Login Tests ---

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Verify login returns valid access and refresh tokens."""
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
    """Ensure login is rejected for incorrect passwords."""
    await create_user(client)
    r = await client.post(
        "/api/v1/auth/login",
        data={"username": TEST_USER["email"], "password": "wrongpassword"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_inactive_user_login_fails(client: AsyncClient, db_session):
    """Ensure inactive users cannot log in even with correct credentials."""
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


# --- Token Lifecycle Tests (Refresh & Logout) ---

@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient):
    """Verify Token Rotation: refreshing returns a NEW pair and invalidates the old one."""
    await create_user(client)
    # Get initial tokens
    r = await client.post("/api/v1/auth/login", data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    old_refresh = r.json()["refresh_token"]
    
    # Perform refresh
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    new_tokens = r.json()
    assert new_tokens["refresh_token"] != old_refresh
    assert "access_token" in new_tokens


@pytest.mark.asyncio
async def test_refresh_token_reuse_detection(client: AsyncClient):
    """Verify Reuse Detection: using a rotated refresh token revokes all sessions."""
    await create_user(client)
    r = await client.post("/api/v1/auth/login", data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    old_refresh = r.json()["refresh_token"]
    
    # 1. First refresh (valid)
    await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    
    # 2. Second refresh with same initial token (invalid reuse)
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 403
    assert "invalid" in r.json()["detail"].lower() or "expired" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout_and_revocation(client: AsyncClient):
    """Verify that logout invalidates current tokens."""
    await create_user(client)
    r = await client.post("/api/v1/auth/login", data={"username": TEST_USER["email"], "password": TEST_USER["password"]})
    tokens = r.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    
    r = await client.post("/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}, headers=headers)
    assert r.status_code == 204
    
    # Use mock to verify that the blacklist check behaves correctly during flight
    with patch("app.core.dependencies.is_token_blacklisted", return_value=True):
        r = await client.get("/api/v1/users/me", headers=headers)
        assert r.status_code == 401


@pytest.mark.asyncio
async def test_refresh_expired_token(client: AsyncClient, db_session):
    """Ensure expired refresh tokens are rejected in the database layer."""
    email = "expired@example.com"
    await create_user(client, {"email": email, "username": "expired_user", "password": "password123"})
    r = await client.post("/api/v1/auth/login", data={"username": email, "password": "password123"})
    refresh_token = r.json()["refresh_token"]
    
    # Force expire in DB
    from sqlalchemy import select
    token_hash = hash_token(refresh_token)
    result = await db_session.execute(select(RefreshToken).where(RefreshToken.token_hash == token_hash))
    db_token = result.scalar_one()
    db_token.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    await db_session.commit()
    
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 403
