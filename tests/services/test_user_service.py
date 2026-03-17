"""
Tests for user service functions.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException

from src.fastapi_training.app.services.user_service import (
    create_user,
    authenticate_user,
    update_user,
)
from src.fastapi_training.app.schemas.user import UserCreate, UserUpdate
from src.fastapi_training.app.db.fake_db import fake_users_db


class TestCreateUser:
    """Tests for user creation."""

    @patch('src.fastapi_training.app.services.user_service.hash_password')
    @patch('src.fastapi_training.app.db.fake_db.fake_users_db', new_callable=list)
    def test_create_user_success(self, mock_db, mock_hash, test_user_data):
        """Test successful user creation."""
        # Setup mock
        mock_hash.return_value = "hashed_test_password_123"
        test_db = []

        # Use real function but with our mock DB
        user_in = UserCreate(**test_user_data)
        user = create_user(user_in)

        assert user["email"] == test_user_data["email"], "User email should match input"
        assert "hashed_password" in user, "User should have hashed_password"
        assert user["hashed_password"] != test_user_data["password"], "Password should be hashed"
        assert len(fake_users_db) == 1, "User should be added to database"

    def test_create_user_duplicate_email(self, test_user_db, test_user_data):
        """Test that creating user with duplicate email raises error."""
        user_in = UserCreate(**test_user_data)

        with pytest.raises(HTTPException) as exc_info:
            create_user(user_in)

        assert exc_info.value.status_code == 400, "Duplicate email should return 400"
        assert "already registered" in exc_info.value.detail, "Error message should mention duplicate"

    def test_create_user_increments_id(self, test_user_data, test_second_user_data):
        """Test that user IDs are incremented correctly."""
        user_in1 = UserCreate(**test_user_data)
        user1 = create_user(user_in1)

        user_in2 = UserCreate(**test_second_user_data)
        user2 = create_user(user_in2)

        assert user1["id"] == 1, "First user should have id 1"
        assert user2["id"] == 2, "Second user should have id 2"
        assert user1["id"] != user2["id"], "User IDs should be different"

    def test_create_user_added_to_db(self, test_user_data):
        """Test that created user is added to database."""
        initial_count = len(fake_users_db)
        user_in = UserCreate(**test_user_data)
        user = create_user(user_in)

        assert len(fake_users_db) == initial_count + \
            1, "Database should increase by 1"
        assert fake_users_db[-1]["email"] == test_user_data["email"], "Last user should be new user"

    @pytest.mark.parametrize("invalid_email", [
        "not-an-email",
        "@example.com",
        "user@",
        "user name@example.com",
        "user@example",
    ])
    def test_create_user_invalid_email(self, invalid_email):
        """Test that creating user with invalid email raises validation error."""
        with pytest.raises(Exception) as exc_info:  # Pydantic validation error
            UserCreate(email=invalid_email, password="ValidPass123")

        assert "email" in str(exc_info.value).lower(
        ), "Error should mention email validation"

    @pytest.mark.parametrize("short_password", [
        "short",
        "pass",
        "123",
        "Pass1!",  # Less than 8 characters
    ])
    def test_create_user_password_too_short(self, short_password):
        """Test that creating user with short password raises validation error."""
        with pytest.raises(Exception) as exc_info:  # Pydantic validation error
            UserCreate(email="test@example.com", password=short_password)

        assert "password" in str(exc_info.value).lower(
        ), "Error should mention password validation"


class TestAuthenticateUser:
    """Tests for user authentication."""

    def test_authenticate_user_success(self, test_user_db, test_user_data):
        """Test successful authentication."""
        user = authenticate_user(
            test_user_data["email"], test_user_data["password"])

        assert user is not None, "Authentication should succeed with correct credentials"
        assert user["id"] == test_user_db["id"], "Should return correct user"
        assert user["email"] == test_user_data["email"], "Should return correct email"

    @pytest.mark.parametrize("wrong_password", [
        "WrongPassword123",
        "Admin@1234",
        "TestPassword124",  # Off by 1
    ])
    def test_authenticate_user_wrong_password(self, test_user_db, test_user_data, wrong_password):
        """Test authentication with various wrong passwords."""
        user = authenticate_user(test_user_data["email"], wrong_password)
        assert user is None, "Authentication should fail with wrong password"

    @pytest.mark.parametrize("nonexistent_email", [
        "nonexistent@example.com",
        "fake@domain.co.uk",
        "notreal@test.org",
    ])
    def test_authenticate_user_nonexistent_email(self, nonexistent_email):
        """Test authentication with non-existent emails."""
        user = authenticate_user(nonexistent_email, "Password123")
        assert user is None, "Authentication should fail with non-existent email"

    @pytest.mark.parametrize("email,password", [
        ("", ""),
        ("", "Password123"),
        ("test@example.com", ""),
    ])
    def test_authenticate_user_empty_credentials(self, email, password):
        """Test authentication with empty credentials."""
        user = authenticate_user(email, password)
        assert user is None, "Authentication should fail with empty credentials"

    def test_authenticate_user_case_sensitive_email(self, test_user_db, test_user_data):
        """Test that email authentication is case-sensitive."""
        # Database has lowercase email
        user = authenticate_user(
            test_user_data["email"].upper(), test_user_data["password"])

        # Should not find user (case-sensitive)
        assert user is None, "Email authentication should be case-sensitive"


class TestUpdateUser:
    """Tests for user updates."""

    def test_update_user_email_only(self, test_user_db, test_user_data):
        """Test updating only email."""
        new_email = "newemail@example.com"
        user_update = UserUpdate(email=new_email, password=None)

        updated_user = update_user(test_user_db["id"], user_update)

        assert updated_user is not None, "Update should return user"
        assert updated_user["email"] == new_email, "Email should be updated"
        assert updated_user["id"] == test_user_db["id"], "ID should not change"

    def test_update_user_password_only(self, test_user_db):
        """Test updating only password."""
        from src.fastapi_training.app.core.security import verify_password

        new_password = "NewPassword123"
        user_update = UserUpdate(email=None, password=new_password)

        updated_user = update_user(test_user_db["id"], user_update)

        # Old password should not work
        assert not verify_password(
            "TestPassword123", updated_user["hashed_password"]), "Old password should not work"
        # New password should work
        assert verify_password(
            new_password, updated_user["hashed_password"]), "New password should work"

    def test_update_user_both_email_and_password(self, test_user_db):
        """Test updating both email and password."""
        from src.fastapi_training.app.core.security import verify_password

        new_email = "newemail@example.com"
        new_password = "NewPassword123"
        user_update = UserUpdate(email=new_email, password=new_password)

        updated_user = update_user(test_user_db["id"], user_update)

        assert updated_user["email"] == new_email, "Email should be updated"
        assert verify_password(
            new_password, updated_user["hashed_password"]), "Password should be updated"

    def test_update_user_nonexistent(self):
        """Test updating non-existent user."""
        user_update = UserUpdate(email="newemail@example.com", password=None)
        updated_user = update_user(999, user_update)

        assert updated_user is None, "Updating non-existent user should return None"

    @pytest.mark.parametrize("new_email", [
        "another@example.com",
        "user.name@domain.co.uk",
        "test+tag@example.com",
    ])
    def test_update_user_different_emails(self, test_user_db, new_email):
        """Test updating user with various valid emails."""
        user_update = UserUpdate(email=new_email, password=None)
        updated_user = update_user(test_user_db["id"], user_update)

        assert updated_user["email"] == new_email, f"Email should be updated to {new_email}"

    @pytest.mark.parametrize("new_password", [
        "NewPass1234",
        "StrongPassword!@#$",
        "AnotherPassword567",
    ])
    def test_update_user_different_passwords(self, test_user_db, new_password):
        """Test updating user with various valid passwords."""
        from src.fastapi_training.app.core.security import verify_password

        user_update = UserUpdate(email=None, password=new_password)
        updated_user = update_user(test_user_db["id"], user_update)

        assert verify_password(
            new_password, updated_user["hashed_password"]), f"Password should be updated"

    def test_update_user_partial_update(self, test_user_db):
        """Test partial update (email unchanged, password changed)."""
        from src.fastapi_training.app.core.security import verify_password

        original_email = test_user_db["email"]
        new_password = "NewPassword123"
        user_update = UserUpdate(email=None, password=new_password)

        updated_user = update_user(test_user_db["id"], user_update)

        assert updated_user["email"] == original_email, "Email should not change"
        assert verify_password(
            new_password, updated_user["hashed_password"]), "Password should be updated"

    def test_update_user_no_changes(self, test_user_db):
        """Test update with no fields specified."""
        user_update = UserUpdate(email=None, password=None)
        original_hash = test_user_db["hashed_password"]

        updated_user = update_user(test_user_db["id"], user_update)

        # Nothing should change
        assert updated_user["email"] == test_user_db["email"], "Email should not change"
        assert updated_user["hashed_password"] == original_hash, "Password should not change"

    def test_update_user_modifies_existing_user(self, test_user_db):
        """Test that update modifies the actual user in database."""
        new_email = "updated@example.com"
        user_update = UserUpdate(email=new_email)

        update_user(test_user_db["id"], user_update)

        # Check database directly
        db_user = fake_users_db[0]
        assert db_user["email"] == new_email
