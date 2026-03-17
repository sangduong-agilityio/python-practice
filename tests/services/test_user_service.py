"""
Tests for user service functions.
"""
import pytest
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

    def test_create_user_success(self, test_user_data):
        """Test successful user creation."""
        user_in = UserCreate(**test_user_data)
        user = create_user(user_in)

        assert user["id"] == 1
        assert user["email"] == test_user_data["email"]
        assert user["hashed_password"] != test_user_data["password"]
        assert len(fake_users_db) == 1

    def test_create_user_duplicate_email(self, test_user_db, test_user_data):
        """Test that creating user with duplicate email raises error."""
        user_in = UserCreate(**test_user_data)

        with pytest.raises(HTTPException) as exc_info:
            create_user(user_in)

        assert exc_info.value.status_code == 400
        assert "already registered" in exc_info.value.detail

    def test_create_user_increments_id(self, test_user_data, test_second_user_data):
        """Test that user IDs are incremented correctly."""
        user_in1 = UserCreate(**test_user_data)
        user1 = create_user(user_in1)

        user_in2 = UserCreate(**test_second_user_data)
        user2 = create_user(user_in2)

        assert user1["id"] == 1
        assert user2["id"] == 2

    def test_create_user_added_to_db(self, test_user_data):
        """Test that created user is added to database."""
        initial_count = len(fake_users_db)
        user_in = UserCreate(**test_user_data)
        user = create_user(user_in)

        assert len(fake_users_db) == initial_count + 1
        assert fake_users_db[-1]["email"] == test_user_data["email"]

    def test_create_user_invalid_email(self):
        """Test that creating user with invalid email raises error."""
        with pytest.raises(Exception):  # Pydantic validation error
            UserCreate(email="invalid-email", password="ValidPass123")

    def test_create_user_password_too_short(self):
        """Test that creating user with short password raises error."""
        with pytest.raises(Exception):  # Pydantic validation error
            UserCreate(email="test@example.com", password="short")


class TestAuthenticateUser:
    """Tests for user authentication."""

    def test_authenticate_user_success(self, test_user_db, test_user_data):
        """Test successful authentication."""
        user = authenticate_user(
            test_user_data["email"], test_user_data["password"])

        assert user is not None
        assert user["id"] == test_user_db["id"]
        assert user["email"] == test_user_data["email"]

    def test_authenticate_user_wrong_password(self, test_user_db, test_user_data):
        """Test authentication with wrong password."""
        user = authenticate_user(test_user_data["email"], "WrongPassword123")

        assert user is None

    def test_authenticate_user_nonexistent_email(self):
        """Test authentication with non-existent email."""
        user = authenticate_user("nonexistent@example.com", "Password123")

        assert user is None

    def test_authenticate_user_empty_credentials(self):
        """Test authentication with empty credentials."""
        user = authenticate_user("", "")

        assert user is None

    def test_authenticate_user_case_sensitive_email(self, test_user_db, test_user_data):
        """Test that email authentication is case-sensitive."""
        # Database has lowercase email
        user = authenticate_user(
            test_user_data["email"].upper(), test_user_data["password"])

        # Should not find user (case-sensitive)
        assert user is None


class TestUpdateUser:
    """Tests for user updates."""

    def test_update_user_email_only(self, test_user_db, test_user_data):
        """Test updating only email."""
        new_email = "newemail@example.com"
        user_update = UserUpdate(email=new_email, password=None)

        updated_user = update_user(test_user_db["id"], user_update)

        assert updated_user["email"] == new_email
        assert updated_user["id"] == test_user_db["id"]

    def test_update_user_password_only(self, test_user_db):
        """Test updating only password."""
        new_password = "NewPassword123"
        user_update = UserUpdate(email=None, password=new_password)

        updated_user = update_user(test_user_db["id"], user_update)

        # Old password should not work
        from src.fastapi_training.app.core.security import verify_password
        assert not verify_password(
            "TestPassword123", updated_user["hashed_password"])
        # New password should work
        assert verify_password(new_password, updated_user["hashed_password"])

    def test_update_user_both_email_and_password(self, test_user_db):
        """Test updating both email and password."""
        new_email = "newemail@example.com"
        new_password = "NewPassword123"
        user_update = UserUpdate(email=new_email, password=new_password)

        updated_user = update_user(test_user_db["id"], user_update)

        assert updated_user["email"] == new_email
        from src.fastapi_training.app.core.security import verify_password
        assert verify_password(new_password, updated_user["hashed_password"])

    def test_update_user_nonexistent(self):
        """Test updating non-existent user."""
        user_update = UserUpdate(email="new@example.com")

        result = update_user(999, user_update)

        assert result is None

    def test_update_user_partial_update(self, test_user_db):
        """Test partial update (email unchanged, password changed)."""
        original_email = test_user_db["email"]
        new_password = "NewPassword123"
        user_update = UserUpdate(email=None, password=new_password)

        updated_user = update_user(test_user_db["id"], user_update)

        assert updated_user["email"] == original_email
        from src.fastapi_training.app.core.security import verify_password
        assert verify_password(new_password, updated_user["hashed_password"])

    def test_update_user_no_changes(self, test_user_db):
        """Test update with no fields specified."""
        user_update = UserUpdate(email=None, password=None)
        original_hash = test_user_db["hashed_password"]

        updated_user = update_user(test_user_db["id"], user_update)

        # Nothing should change
        assert updated_user["email"] == test_user_db["email"]
        assert updated_user["hashed_password"] == original_hash

    def test_update_user_modifies_existing_user(self, test_user_db):
        """Test that update modifies the actual user in database."""
        new_email = "updated@example.com"
        user_update = UserUpdate(email=new_email)

        update_user(test_user_db["id"], user_update)

        # Check database directly
        db_user = fake_users_db[0]
        assert db_user["email"] == new_email
