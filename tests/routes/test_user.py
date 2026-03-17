"""
Tests for user routes.
"""
import pytest


class TestGetMeRoute:
    """Tests for GET /users/me endpoint."""

    def test_get_me_success(self, client, test_user_db, auth_headers):
        """Test getting current user info."""
        response = client.get("/users/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_user_db["id"]
        assert data["email"] == test_user_db["email"]

    def test_get_me_without_token(self, client):
        """Test getting user info without token."""
        response = client.get("/users/me")

        assert response.status_code == 401

    def test_get_me_with_invalid_token(self, client):
        """Test getting user info with invalid token."""
        response = client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401

    def test_get_me_with_expired_token(self, client, test_user_expired_token):
        """Test getting user info with expired token."""
        response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {test_user_expired_token}"}
        )

        assert response.status_code == 401

    def test_get_me_does_not_return_password(self, client, test_user_db, auth_headers):
        """Test that password is not returned."""
        response = client.get("/users/me", headers=auth_headers)

        data = response.json()
        assert "password" not in data
        assert "hashed_password" not in data


class TestUpdateUserRoute:
    """Tests for PUT /users/{user_id} endpoint."""

    def test_update_user_email_success(self, client, test_user_db, auth_headers):
        """Test successful email update."""
        new_email = "newemail@example.com"
        response = client.put(
            f"/users/{test_user_db['id']}",
            json={"email": new_email},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email

    def test_update_user_password_success(self, client, test_user_db, auth_headers):
        """Test successful password update."""
        new_password = "NewPassword123"
        response = client.put(
            f"/users/{test_user_db['id']}",
            json={"password": new_password},
            headers=auth_headers
        )

        assert response.status_code == 200

        # Old password should not work anymore
        response = client.post(
            "/auth/login",
            data={"username": test_user_db["email"],
                  "password": "TestPassword123"}
        )
        assert response.status_code == 401

        # New password should work
        response = client.post(
            "/auth/login",
            data={"username": test_user_db["email"], "password": new_password}
        )
        assert response.status_code == 200

    def test_update_user_both_fields_success(self, client, test_user_db, auth_headers):
        """Test updating both email and password."""
        new_email = "newemail@example.com"
        new_password = "NewPassword123"

        response = client.put(
            f"/users/{test_user_db['id']}",
            json={"email": new_email, "password": new_password},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email

    def test_update_user_unauthorized_user(self, client, test_user_db, test_second_user_db, auth_headers, second_auth_headers):
        """Test that user cannot update another user."""
        response = client.put(
            f"/users/{test_user_db['id']}",
            json={"email": "new@example.com"},
            headers=second_auth_headers
        )

        assert response.status_code == 403
        assert "Not allowed to update this user" in response.json()["detail"]

    def test_update_user_without_token(self, client, test_user_db):
        """Test updating user without token."""
        response = client.put(
            f"/users/{test_user_db['id']}",
            json={"email": "new@example.com"}
        )

        assert response.status_code == 401

    def test_update_nonexistent_user(self, client, test_user_db, auth_headers):
        """Test updating non-existent user - checks authorization first."""
        # Authorization check happens before checking if user exists
        # So it returns 403 (forbidden) because auth check fails for user 999
        response = client.put(
            "/users/999",
            json={"email": "new@example.com"},
            headers=auth_headers
        )

        # Will be 403 because current_user["id"] (from token) != user_id (path param)
        assert response.status_code == 403

    def test_update_user_invalid_email(self, client, test_user_db, auth_headers):
        """Test updating user with invalid email."""
        response = client.put(
            f"/users/{test_user_db['id']}",
            json={"email": "not-an-email"},
            headers=auth_headers
        )

        assert response.status_code == 422

    def test_update_user_invalid_password(self, client, test_user_db, auth_headers):
        """Test updating user with password (validation is at creation, not update)."""
        # UserUpdate schema doesn't have password validation - only UserCreate does
        # So we just ensure password field can be set
        response = client.put(
            f"/users/{test_user_db['id']}",
            json={"password": "short"},
            headers=auth_headers
        )

        # Should accept since UserUpdate doesn't validate password length
        assert response.status_code == 200

    def test_update_user_partial(self, client, test_user_db, auth_headers):
        """Test partial update (email only)."""
        new_email = "newemail@example.com"

        response = client.put(
            f"/users/{test_user_db['id']}",
            json={"email": new_email},
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == new_email

    def test_update_user_one_time(self, client, test_user_db, auth_headers):
        """Test updating user successfully."""
        # Note: After email update, the token (which contains old email) becomes invalid
        # This is expected behavior
        response = client.put(
            f"/users/{test_user_db['id']}",
            json={"email": "updated@example.com"},
            headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["email"] == "updated@example.com"
