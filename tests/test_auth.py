"""
Test Authentication Flow

Cover:
- Register
- Login
- Protected route
"""

import pytest
from fastapi import status


class TestAuthRegister:
    """Test user registration endpoint."""

    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["id"] == 2  # Second user

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": test_user["email"],
                "password": "anotherpassword123"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response.json()["detail"].lower()

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "invalidemail",  # Missing @domain
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_missing_password(self, client):
        """Test registration without password fails."""
        response = client.post(
            "/auth/register",
            json={
                "email": "user@example.com"
                # Missing password
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogin:
    """Test user login (token) endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login returns access token."""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user["email"],
                "password": "wrongpassword"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Incorrect" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email fails."""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_login_response_format(self, client, test_user):
        """Test login response has correct format."""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data["access_token"], str)
        assert len(data["access_token"]) > 0
        assert data["token_type"].lower() == "bearer"


class TestProtectedRoutes:
    """Test access control for protected routes."""

    def test_get_current_user_with_valid_token(self, client, auth_headers):
        """Test accessing protected route with valid token."""
        response = client.get(
            "/users/me",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["id"] == 1

    def test_get_current_user_without_token(self, client):
        """Test accessing protected route without token fails."""
        response = client.get("/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_with_invalid_token(self, client):
        """Test accessing protected route with invalid token fails."""
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_with_expired_token(self, client):
        """Test accessing protected route with malformed token fails."""
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer malformed"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_tasks_without_token(self, client):
        """Test getting tasks without token fails."""
        response = client.get("/tasks/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_tasks_with_valid_token(self, client, auth_headers):
        """Test getting tasks with valid token succeeds."""
        response = client.get(
            "/tasks/",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.json(), list)


class TestTokenExpiration:
    """
    Test token expiration and refresh workflow.

    Purpose:
    - Verify expired token returns 401
    - Verify refresh token can generate new access token
    """

    def test_refresh_token_returns_new_access_token(self, client, test_user):
        """Test refresh token returns a new access token."""

        # Login to get tokens
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user["email"],
                "password": test_user["password"]
            }
        )

        assert login_response.status_code == status.HTTP_200_OK

        tokens = login_response.json()
        refresh_token = tokens["refresh_token"]

        # Call refresh endpoint
        refresh_response = client.post(
            "/auth/refresh",
            data={
                "username": "dummy",
                "password": refresh_token
            }
        )

        assert refresh_response.status_code == status.HTTP_200_OK
        new_access_token = refresh_response.json()["access_token"]

        # Use new token to access protected route
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["email"] == test_user["email"]

    def test_invalid_refresh_token(self, client):
        """Test invalid refresh token returns 401."""

        response = client.post(
            "/auth/refresh",
            data={
                "username": "dummy",
                "password": "invalid_token"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_verify_token_expired(self):
        """Test verify_token raises error for expired token."""

        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from fastapi import HTTPException
        from src.fastapi_training.app.core.config import settings
        from src.fastapi_training.app.core.security import verify_token

        expired_payload = {
            "sub": "test@example.com",
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1)
        }

        expired_token = jwt.encode(
            expired_payload,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )

        try:
            verify_token(expired_token)
            assert False
        except HTTPException as e:
            assert e.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthenticationFlow:
    """Test complete authentication workflow."""

    def test_full_auth_flow(self, client):
        """Test complete flow: register -> login -> access protected route."""
        # Step 1: Register
        register_response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123"
            }
        )
        assert register_response.status_code == status.HTTP_201_CREATED

        # Step 2: Login
        login_response = client.post(
            "/auth/login",
            data={
                "username": "newuser@example.com",
                "password": "securepass123"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        token = login_response.json()["access_token"]

        # Step 3: Access protected route
        protected_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert protected_response.status_code == status.HTTP_200_OK
        assert protected_response.json()["email"] == "newuser@example.com"
