import pytest
from unittest.mock import AsyncMock, patch
from fastapi import HTTPException, status
from src.fastapi_training.services.auth_service import login, refresh, logout
from src.fastapi_training.models.user import User
from src.fastapi_training.models.refresh_token import RefreshToken
from src.fastapi_training.core.security import TokenError

# We don't need a real DB session; we'll pass None and mock the CRUD layers.
# This demonstrates a "pure unit test" for the Service Layer.

@pytest.fixture
def mock_db():
    return None

@pytest.mark.asyncio
class TestAuthService:
    
    @patch("src.fastapi_training.services.auth_service.user_crud.get_user_by_email", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.auth_service.verify_password")
    @patch("src.fastapi_training.services.auth_service.rt_crud.create_refresh_token", new_callable=AsyncMock)
    async def test_login_success(self, mock_create_rt, mock_verify_password, mock_get_user, mock_db):
        """Test login service logic on success."""
        # Setup mocks
        mock_user = User(id=1, email="test@example.com", hashed_password="hashed_pass")
        mock_get_user.return_value = mock_user
        mock_verify_password.return_value = True

        # Call service
        response = await login(mock_db, email="test@example.com", password="correct_password")

        # Assertions
        assert response.token_type == "bearer"
        assert response.access_token is not None
        assert response.refresh_token is not None
        
        # Verify CRUD was called correctly
        mock_get_user.assert_called_once_with(mock_db, email="test@example.com")
        mock_verify_password.assert_called_once_with("correct_password", "hashed_pass")
        mock_create_rt.assert_called_once()


    @patch("src.fastapi_training.services.auth_service.user_crud.get_user_by_email", new_callable=AsyncMock)
    @patch("src.fastapi_training.services.auth_service.verify_password")
    async def test_login_wrong_password(self, mock_verify_password, mock_get_user, mock_db):
        """Test login fails with incorrect password."""
        mock_user = User(id=1, email="test@example.com", hashed_password="hashed_pass")
        mock_get_user.return_value = mock_user
        mock_verify_password.return_value = False  # Wrong password

        with pytest.raises(HTTPException) as exc_info:
            await login(mock_db, email="test@example.com", password="wrong_password")
            
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Incorrect email or password"


    @patch("src.fastapi_training.services.auth_service.verify_token")
    @patch("src.fastapi_training.services.auth_service.rt_crud.get_refresh_token", new_callable=AsyncMock)
    async def test_refresh_success(self, mock_get_rt, mock_verify_token, mock_db):
        """Test refresh service issues new token successfully."""
        from datetime import datetime, timezone, timedelta
        mock_verify_token.return_value = {"sub": "test@example.com"}
        
        mock_token_record = RefreshToken(
            id=1, token="hashed", user_id=1, is_revoked=False, expires_at=datetime.now(timezone.utc) + timedelta(days=1)
        )
        mock_get_rt.return_value = mock_token_record

        # Call service
        response = await refresh(mock_db, refresh_token_str="fake_token")

        assert response.access_token is not None
        assert response.token_type == "bearer"


    @patch("src.fastapi_training.services.auth_service.verify_token")
    @patch("src.fastapi_training.services.auth_service.rt_crud.get_refresh_token", new_callable=AsyncMock)
    async def test_refresh_revoked_token(self, mock_get_rt, mock_verify_token, mock_db):
        """Test refresh fails if token is revoked."""
        mock_verify_token.return_value = {"sub": "test@example.com"}
        
        # Token exists but is revoked!
        mock_token_record = RefreshToken(
            id=1, token="hashed", user_id=1, is_revoked=True
        )
        mock_get_rt.return_value = mock_token_record

        with pytest.raises(HTTPException) as exc_info:
            await refresh(mock_db, refresh_token_str="fake_token")
            
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Refresh token has been revoked"


    @patch("src.fastapi_training.services.auth_service.verify_token")
    async def test_refresh_invalid_signature(self, mock_verify_token, mock_db):
        """Test refresh fails if JWT signature is invalid."""
        mock_verify_token.side_effect = TokenError("Bad signature")

        with pytest.raises(HTTPException) as exc_info:
            await refresh(mock_db, refresh_token_str="fake_token")
            
        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc_info.value.detail == "Invalid or expired refresh token"
