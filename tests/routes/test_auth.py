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

        assert response.status_code == 201, "Registration should return 201"
        data = response.json()
        assert data["email"] == test_user_data["email"], "Response should contain registered email"
        assert "id" in data, "Response should contain user ID"
        # Password should not be returned
        assert "password" not in data, "Password should not be in response"
        assert "hashed_password" not in data, "Hashed password should not be in response"

    def test_register_duplicate_email(self, client, test_user_db, test_user_data):
        """Test registration with duplicate email."""
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == 400, "Duplicate email should return 400"
        error = response.json()
        assert "already registered" in error["detail"], "Error message should mention duplicate"

    @pytest.mark.parametrize("invalid_email", [
        "not-an-email",
        "@example.com",
        "user@",
        "user name@example.com",
    ])
    def test_register_invalid_email(self, client, invalid_email):
        """Test registration with invalid email formats."""
        response = client.post(
            "/auth/register",
            json={"email": invalid_email, "password": "ValidPass123"}
        )

        assert response.status_code == 422, "Invalid email should return 422 (validation error)"

    @pytest.mark.parametrize("short_password", [
        "short",
        "pass",
        "123456",
        "Pass1!",  # Less than 8 characters
    ])
    def test_register_password_too_short(self, client, short_password):
        """Test registration with password shorter than 8 characters."""
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": short_password}
        )

        assert response.status_code == 422, "Short password should return 422"

    def test_register_multiple_users(self, client, test_user_data, test_second_user_data):
        """Test registering multiple users."""
        # Register first user
        response1 = client.post("/auth/register", json=test_user_data)
        assert response1.status_code == 201, "First registration should succeed"
        user1_id = response1.json()["id"]

        # Register second user
        response2 = client.post("/auth/register", json=test_second_user_data)
        assert response2.status_code == 201, "Second registration should succeed"
        user2_id = response2.json()["id"]

        # IDs should be different
        assert user1_id != user2_id, "Different users should have different IDs"


class TestLoginRoute:
    """Tests for /auth/login endpoint."""

    def test_login_success(self, client, test_user_db, test_user_data):
        """Test successful login."""
        response = client.post(
            "/auth/login",
            data={"username": test_user_data["email"],
                  "password": test_user_data["password"]}
        )

        assert response.status_code == 200, "Login should return 200"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "refresh_token" in data, "Response should contain refresh_token"
        assert data["token_type"] == "bearer", "Token type should be bearer"

    @pytest.mark.parametrize("wrong_password", [
        "WrongPassword123",
        "Admin@1234",
        "TestPassword124",
    ])
    def test_login_wrong_password(self, client, test_user_db, test_user_data, wrong_password):
        """Test login with various wrong passwords."""
        response = client.post(
            "/auth/login",
            data={"username": test_user_data["email"],
                  "password": wrong_password}
        )

        assert response.status_code == 401, "Wrong password should return 401"
        assert "Incorrect email or password" in response.json(
        )["detail"], "Should have proper error message"

    @pytest.mark.parametrize("nonexistent_email", [
        "nonexistent@example.com",
        "fake@domain.co.uk",
        "notreal@test.org",
    ])
    def test_login_nonexistent_user(self, client, nonexistent_email):
        """Test login with non-existent email."""
        response = client.post(
            "/auth/login",
            data={"username": nonexistent_email,
                  "password": "Password123"}
        )

        assert response.status_code == 401, "Non-existent user should return 401"
        assert "Incorrect email or password" in response.json(
        )["detail"], "Should have proper error message"

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
        assert isinstance(access_token, str) and len(
            access_token) > 0, "Access token should be non-empty string"
        assert isinstance(refresh_token, str) and len(
            refresh_token) > 0, "Refresh token should be non-empty string"

        # Both should have JWT format (3 parts separated by dots)
        assert access_token.count(
            ".") == 2, "Access token should have JWT format"
        assert refresh_token.count(
            ".") == 2, "Refresh token should have JWT format"

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
        assert response.status_code == 401, "Uppercase email should not match lowercase email"


class TestRefreshRoute:
    """Tests for /auth/refresh endpoint."""

    def test_refresh_success(self, client, test_user_db, test_user_refresh_token):
        """Test successful token refresh."""
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": test_user_refresh_token},
        )

        assert response.status_code == 200, "Refresh should return 200"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert data["token_type"] == "bearer", "Token type should be bearer"
        # Refresh token returns only access token, not refresh token
        assert "refresh_token" not in data, "Should not return refresh_token on refresh endpoint"

    @pytest.mark.parametrize("invalid_token", [
        "invalid.token.here",
        "completely-invalid",
        "too.many.dots.here.now",
    ])
    def test_refresh_with_invalid_token(self, client, invalid_token):
        """Test refresh with invalid tokens."""
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": invalid_token},
        )

        # Should fail - either 401 from token validation or 422 from form validation
        assert response.status_code in (
            401, 422), "Invalid token should fail with 401 or 422"

    def test_refresh_with_expired_token(self, client, test_user_expired_token):
        """Test refresh with expired token."""
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": test_user_expired_token},
        )

        # Should fail - either 401 from token validation or 422 from form validation
        assert response.status_code in (
            401, 422), "Expired token should fail with 401 or 422"

    def test_refresh_returns_valid_token(self, client, test_user_db, test_user_refresh_token):
        """Test that returned token is valid and can be used."""
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": test_user_refresh_token},
        )

        assert response.status_code == 200, "Refresh should succeed"
        new_access_token = response.json()["access_token"]

        # Use the new token to access protected route
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )

        assert response.status_code == 200, "New token should work for protected routes"
        assert response.json()[
            "email"] == test_user_db["email"], "Should return correct user"

    def test_refresh_token_format(self, client, test_user_db, test_user_refresh_token):
        """Test that returned token has valid JWT format."""
        response = client.post(
            "/auth/refresh",
            data={"username": "user", "password": test_user_refresh_token},
        )

        assert response.status_code == 200, "Refresh should succeed"
        token = response.json()["access_token"]

        # Should have JWT format
        assert token.count(
            ".") == 2, "Token should have JWT format with 3 parts"
        assert isinstance(token, str), "Token should be string"
        assert len(token) > 0, "Token should not be empty"
