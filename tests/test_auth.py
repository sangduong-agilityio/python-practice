"""
tests/test_auth.py
------------------
Tests for /auth/register and /auth/login endpoints.

Each test function tests exactly ONE behavior.
Test names follow: test_<endpoint>_<scenario>
"""

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Registration tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """Happy path: valid data returns 201 with user profile (no password)."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "username": "alice",
            "password": "securepassword123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "alice@example.com"
    assert data["username"] == "alice"
    assert "hashed_password" not in data  # NEVER expose password hash
    assert "id" in data
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Registering with an already-used email returns 400."""
    payload = {
        "email": "dup@example.com",
        "username": "user1",
        "password": "password123",
    }
    # First registration should succeed
    await client.post("/api/v1/auth/register", json=payload)

    # Second registration with same email should fail
    payload["username"] = "user2"
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "email" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient) -> None:
    """Registering with an already-used username returns 400."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "first@example.com", "username": "samename", "password": "pass12345"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "second@example.com", "username": "samename", "password": "pass12345"},
    )
    assert response.status_code == 400
    assert "username" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_short_password_422(client: AsyncClient) -> None:
    """Password shorter than 8 characters fails Pydantic validation (422)."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "x@x.com", "username": "xuser", "password": "short"},
    )
    assert response.status_code == 422  # Unprocessable Entity


@pytest.mark.asyncio
async def test_register_invalid_email_422(client: AsyncClient) -> None:
    """Invalid email format fails Pydantic validation (422)."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "username": "xuser", "password": "password123"},
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Happy path: valid credentials return a JWT token."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "username": "loginuser", "password": "mypassword99"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "username": "loginuser", "password": "mypassword99"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20  # Sanity check — JWTs are long strings


@pytest.mark.asyncio
async def test_login_wrong_password_401(client: AsyncClient) -> None:
    """Wrong password returns 401 Unauthorized."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wp@example.com", "username": "wpuser", "password": "correctpassword"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wp@example.com", "username": "wpuser", "password": "WRONGPASSWORD"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user_401(client: AsyncClient) -> None:
    """Logging in with an email that doesn't exist returns 401."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ghost@example.com", "username": "ghost", "password": "doesntmatter"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# Protected endpoint tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_me_authenticated(client: AsyncClient, auth_headers: dict) -> None:
    """GET /users/me with a valid token returns the user's profile."""
    response = await client.get("/api/v1/users/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["username"] == "testuser"


@pytest.mark.asyncio
async def test_get_me_no_token_401(client: AsyncClient) -> None:
    """GET /users/me without a token returns 401."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me_invalid_token_401(client: AsyncClient) -> None:
    """GET /users/me with a garbage token returns 401."""
    response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": "Bearer this.is.garbage"},
    )
    assert response.status_code == 401
