"""Tests for user service."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.fastapi_training.services import user_service
from src.fastapi_training.models.user import User
from src.fastapi_training.schemas.user import UserCreate, UserUpdate


@pytest.fixture
def mock_db() -> AsyncSession:
    """Mock database session."""
    return None


@pytest.mark.asyncio
class TestUserService:
    """Test cases for user service business logic."""

    @patch("src.fastapi_training.services.user_service.user_crud.get_user_by_email", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.user_service.user_crud.create_user_db", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.user_service.hash_password")
    async def test_create_user_success(self, mock_hash, mock_create_db, mock_get_email, mock_db):
        """Test creating a new user successfully."""
        # Setup
        mock_get_email.return_value = None  # Email doesn't exist yet
        mock_hash.return_value = "hashed_password_123"
        mock_user = User(id=1, email="newuser@example.com",
                         hashed_password="hashed_password_123")
        mock_create_db.return_value = mock_user

        # Execute
        user_in = UserCreate(email="newuser@example.com",
                             password="password123")
        result = await user_service.create_user(mock_db, user_in)

        # Assert
        assert result.email == "newuser@example.com"
        mock_get_email.assert_called_once()
        mock_hash.assert_called_once_with("password123")
        mock_create_db.assert_called_once()

    @patch("src.fastapi_training.services.user_service.user_crud.get_user_by_email", new_callable=AsyncMock)
    async def test_create_user_email_exists(self, mock_get_email, mock_db):
        """Test create user fails if email already registered."""
        # Setup - email already exists
        existing_user = User(
            id=1, email="existing@example.com", hashed_password="hashed")
        mock_get_email.return_value = existing_user

        # Execute & Assert
        user_in = UserCreate(email="existing@example.com",
                             password="password123")
        with pytest.raises(HTTPException) as exc_info:
            await user_service.create_user(mock_db, user_in)

        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert exc_info.value.detail == "Email already registered"

    @patch("src.fastapi_training.services.user_service.user_crud.get_user_by_email", new_callable=AsyncMock)
    async def test_get_user_by_email(self, mock_get_email, mock_db):
        """Test retrieving user by email."""
        # Setup
        mock_user = User(id=1, email="test@example.com",
                         hashed_password="hashed")
        mock_get_email.return_value = mock_user

        # Execute
        result = await user_service.get_user_by_email(mock_db, "test@example.com")

        # Assert
        assert result.email == "test@example.com"
        mock_get_email.assert_called_once_with(
            mock_db, email="test@example.com")

    @patch("src.fastapi_training.services.user_service.user_crud.get_user_by_email", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.user_service.verify_password")
    async def test_authenticate_user_success(self, mock_verify, mock_get_email, mock_db):
        """Test user authentication with correct password."""
        # Setup
        mock_user = User(id=1, email="test@example.com",
                         hashed_password="hashed")
        mock_get_email.return_value = mock_user
        mock_verify.return_value = True

        # Execute
        result = await user_service.authenticate_user(mock_db, "test@example.com", "password123")

        # Assert
        assert result.id == 1
        mock_verify.assert_called_once_with("password123", "hashed")

    @patch("src.fastapi_training.services.user_service.user_crud.get_user_by_email", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.user_service.verify_password")
    async def test_authenticate_user_wrong_password(self, mock_verify, mock_get_email, mock_db):
        """Test authentication fails with wrong password."""
        # Setup
        mock_user = User(id=1, email="test@example.com",
                         hashed_password="hashed")
        mock_get_email.return_value = mock_user
        mock_verify.return_value = False

        # Execute
        result = await user_service.authenticate_user(mock_db, "test@example.com", "wrong_password")

        # Assert
        assert result is None
        mock_verify.assert_called_once()

    @patch("src.fastapi_training.services.user_service.user_crud.get_user", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.user_service.user_crud.update_user_db", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.user_service.hash_password")
    async def test_update_user_password(self, mock_hash, mock_update_db, mock_get_user, mock_db):
        """Test updating user password."""
        # Setup
        old_user = User(id=1, email="test@example.com",
                        hashed_password="old_hash")
        mock_get_user.return_value = old_user
        mock_hash.return_value = "new_hash"
        updated_user = User(id=1, email="test@example.com",
                            hashed_password="new_hash")
        mock_update_db.return_value = updated_user

        # Execute
        user_update = UserUpdate(password="newpassword123")
        result = await user_service.update_user(mock_db, 1, user_update)

        # Assert
        assert result.hashed_password == "new_hash"
        mock_hash.assert_called_once_with("newpassword123")
        mock_update_db.assert_called_once()
