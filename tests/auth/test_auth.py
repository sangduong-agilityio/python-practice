"""
Tests for authentication routes.
"""
import pytest
from src.fastapi_training.app.schemas.user import UserCreate


class TestRegisterRoute:
    """Tests for /auth/register endpoint."""

    def test_register_success(self, client, test_user_data):
        """Test successful user registration."""
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        # Password should not be returned
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user_db, test_user_data):
        """Test registration with duplicate email."""
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "ValidPass123"}
        )

        assert response.status_code == 422  # Validation error

    def test_register_password_too_short(self, client):
        """Test registration with password shorter than 8 characters."""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": "short"}
        )

        assert response.status_code == 422

    def test_register_multiple_users(self, client, test_user_data, test_second_user_data):
        """Test registering multiple users."""
        # Register first user
        response1 = client.post("/auth/register", json=test_user_data)
        assert response1.status_code == 201
        user1_id = response1.json()["id"]

        # Register second user
        response2 = client.post("/auth/register", json=test_second_user_data)
        assert response2.status_code == 201
        user2_id = response2.json()["id"]

        # IDs should be different
        assert user1_id != user2_id


class TestLoginRoute:
    """Tests for /auth/login endpoint."""

    def test_login_success(self, client, test_user_data):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            data={"username": test_user_data["email"],
                  "password": test_user_data["password"]}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, test_user_db, test_user_data):
        """Test login with wrong password."""
        response = client.post(
            "/auth/login",
            data={"username": test_user_data["email"],
                  "password": "WrongPassword123"}
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent email."""
        response = client.post(
            "/auth/login",
            data={"username": "nonexistent@example.com",
                  "password": "Password123"}
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    def test_login_returns_valid_tokens(self, client, test_user_db, test_user_data):
        """Test that returned tokens are valid JWT tokens."""
        response = client.post(
            "/auth/login",
            data={"username": test_user_data["email"],
                  "password": test_user_data["password"]}
        )

        tokens = response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Tokens should be non-empty strings
        assert isinstance(access_token, str) and len(access_token) > 0
        assert isinstance(refresh_token, str) and len(refresh_token) > 0

        # Both should have JWT format (3 parts separated by dots)
        assert access_token.count(".") == 2
        assert refresh_token.count(".") == 2

    def test_login_case_sensitive_email(self, client, test_user_db, test_user_data):
        """Test that login email is case-sensitive."""
        response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"].upper(),
                "password": test_user_data["password"]
            }
        )

        # Should fail due to case-sensitive email lookup
        assert response.status_code == 401


class TestRefreshRoute:
    """Tests for /auth/refresh endpoint."""

    def test_refresh_success(self, client, test_user_db, test_user_refresh_token):
        """Test successful token refresh."""
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": test_user_refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Refresh token returns only access token, not refresh token
        assert "refresh_token" not in data

    def test_refresh_with_invalid_token(self, client):
        """Test refresh with invalid token."""
        # OAuth2PasswordRequestForm might reject this before reaching validation
        # So we just ensure it doesn't succeed
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": "invalid.token.here"},
        )

        # Should fail - either 401 from token validation or 422 from form validation
        assert response.status_code in (401, 422)

    def test_refresh_with_expired_token(self, client, test_user_expired_token):
        """Test refresh with expired token."""
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": test_user_expired_token},
        )

        # Should fail - either 401 from token validation or 422 from form validation
        assert response.status_code in (401, 422)

    def test_refresh_returns_valid_token(self, client, test_user_db, test_user_refresh_token):
        """Test that returned token is valid and can be used."""
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": test_user_refresh_token},
        )

        assert response.status_code == 200
        new_access_token = response.json()["access_token"]

        # Use the new token to access protected route
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )

        assert response.status_code == 200
        assert response.json()["email"] == test_user_db["email"]

    def test_refresh_token_format(self, client, test_user_db, test_user_refresh_token):
        """Test that returned token has valid JWT format."""
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": test_user_refresh_token},
        )

        assert response.status_code == 200
        token = response.json()["access_token"]

        # Should have JWT format
        assert token.count(".") == 2
        assert isinstance(token, str)
