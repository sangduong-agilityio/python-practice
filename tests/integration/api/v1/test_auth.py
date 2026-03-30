"""
Integration tests for authentication routes.
"""
import pytest
from src.fastapi_training.schemas.user import UserCreate


class TestRegisterRoute:
    """Tests for /auth/register endpoint."""

    def test_register_success(self, client, test_user_data):
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert "id" in data
        assert "password" not in data
        assert "hashed_password" not in data

    def test_register_duplicate_email(self, client, test_user_db, test_user_data):
        response = client.post("/auth/register", json=test_user_data)

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.parametrize("invalid_email", [
        "not-an-email", "@example.com", "user@", "user name@example.com",
    ])
    def test_register_invalid_email(self, client, invalid_email):
        response = client.post(
            "/auth/register",
            json={"email": invalid_email, "password": "ValidPass123"},
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("short_password", [
        "short", "pass", "123456", "Pass1!",
    ])
    def test_register_password_too_short(self, client, short_password):
        response = client.post(
            "/auth/register",
            json={"email": "test@example.com", "password": short_password},
        )
        assert response.status_code == 422

    def test_register_multiple_users(self, client, test_user_data, test_second_user_data):
        r1 = client.post("/auth/register", json=test_user_data)
        assert r1.status_code == 201
        r2 = client.post("/auth/register", json=test_second_user_data)
        assert r2.status_code == 201
        assert r1.json()["id"] != r2.json()["id"]


class TestLoginRoute:
    """Tests for /auth/login endpoint."""

    def test_login_success(self, client, test_user_db, test_user_data):
        response = client.post(
            "/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.parametrize("wrong_password", [
        "WrongPassword123", "Admin@1234", "TestPassword124",
    ])
    def test_login_wrong_password(self, client, test_user_db, test_user_data, wrong_password):
        response = client.post(
            "/auth/login",
            data={"username": test_user_data["email"], "password": wrong_password},
        )
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    @pytest.mark.parametrize("nonexistent_email", [
        "nonexistent@example.com", "fake@domain.co.uk", "notreal@test.org",
    ])
    def test_login_nonexistent_user(self, client, nonexistent_email):
        response = client.post(
            "/auth/login",
            data={"username": nonexistent_email, "password": "Password123"},
        )
        assert response.status_code == 401

    def test_login_returns_valid_tokens(self, client, test_user_db, test_user_data):
        response = client.post(
            "/auth/login",
            data={"username": test_user_data["email"], "password": test_user_data["password"]},
        )
        tokens = response.json()
        assert tokens["access_token"].count(".") == 2
        assert tokens["refresh_token"].count(".") == 2

    def test_login_case_sensitive_email(self, client, test_user_db, test_user_data):
        response = client.post(
            "/auth/login",
            data={"username": test_user_data["email"].upper(), "password": test_user_data["password"]},
        )
        assert response.status_code == 401


class TestRefreshRoute:
    """Tests for /auth/refresh endpoint."""

    def test_refresh_success(self, client, test_user_db, test_user_refresh_token):
        response = client.post("/auth/refresh", json={"refresh_token": test_user_refresh_token})
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" not in data

    @pytest.mark.parametrize("invalid_token", [
        "invalid.token.here", "completely-invalid", "too.many.dots.here.now",
    ])
    def test_refresh_with_invalid_token(self, client, invalid_token):
        response = client.post("/auth/refresh", json={"refresh_token": invalid_token})
        assert response.status_code in (401, 422)

    def test_refresh_with_expired_token(self, client, test_user_expired_token):
        response = client.post("/auth/refresh", json={"refresh_token": test_user_expired_token})
        assert response.status_code in (401, 422)

    def test_refresh_returns_valid_token(self, client, test_user_db, test_user_refresh_token):
        response = client.post("/auth/refresh", json={"refresh_token": test_user_refresh_token})
        assert response.status_code == 200
        new_access_token = response.json()["access_token"]

        r = client.get("/users/me", headers={"Authorization": f"Bearer {new_access_token}"})
        assert r.status_code == 200
        assert r.json()["email"] == test_user_db["email"]

    def test_refresh_with_revoked_token(self, client, test_user_db, test_user_refresh_token):
        """A token that has been revoked via logout must not be usable for refresh."""
        # Revoke the token first
        logout_response = client.post("/auth/logout", json={"refresh_token": test_user_refresh_token})
        assert logout_response.status_code == 204

        # Now try to use it — should be rejected
        refresh_response = client.post("/auth/refresh", json={"refresh_token": test_user_refresh_token})
        assert refresh_response.status_code == 401


class TestLogoutRoute:
    """Tests for /auth/logout endpoint."""

    def test_logout_success(self, client, test_user_db, test_user_refresh_token):
        """Logout should return 204 No Content."""
        response = client.post("/auth/logout", json={"refresh_token": test_user_refresh_token})
        assert response.status_code == 204

    def test_logout_then_refresh_fails(self, client, test_user_db, test_user_refresh_token):
        """After logout, the same refresh token must not produce a new access token."""
        client.post("/auth/logout", json={"refresh_token": test_user_refresh_token})

        response = client.post("/auth/refresh", json={"refresh_token": test_user_refresh_token})
        assert response.status_code == 401

    def test_logout_with_unknown_token_is_ok(self, client):
        """Logout is idempotent — unknown tokens should not cause errors."""
        response = client.post("/auth/logout", json={"refresh_token": "unknown.token.here"})
       
        assert response.status_code == 204
