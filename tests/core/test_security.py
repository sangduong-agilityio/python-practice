"""
Tests for security module (JWT and password hashing).
"""
import pytest
from datetime import timedelta
from jose import JWTError, jwt

from src.fastapi_training.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from src.fastapi_training.app.core.config import settings
from fastapi import HTTPException


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password(self):
        """Test password hashing."""
        password = "MySecurePassword123"
        hashed = hash_password(password)

        # Hash should not be equal to original password
        assert hashed != password
        # Hash should be a string
        assert isinstance(hashed, str)

    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "MySecurePassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with wrong password."""
        password = "MySecurePassword123"
        wrong_password = "WrongPassword123"
        hashed = hash_password(password)

        assert verify_password(wrong_password, hashed) is False

    def test_verify_password_empty(self):
        """Test password verification with empty password."""
        password = "MySecurePassword123"
        hashed = hash_password(password)

        assert verify_password("", hashed) is False

    def test_hash_same_password_different_hashes(self):
        """Test that hashing same password produces different hashes (due to salt)."""
        password = "MySecurePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different (salted)
        assert hash1 != hash2
        # Both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestAccessToken:
    """Tests for access token creation and verification."""

    def test_create_access_token(self):
        """Test creating access token."""
        data = {"sub": "test@example.com"}
        token = create_access_token(data)

        # Token should be a string
        assert isinstance(token, str)
        # Token should not be empty
        assert len(token) > 0

    def test_create_access_token_with_custom_expiration(self):
        """Test creating access token with custom expiration time."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(hours=2)
        token = create_access_token(data, expires_delta)

        # Decode and verify expiration
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert "exp" in payload
        assert payload["sub"] == "test@example.com"

    def test_create_access_token_contains_subject(self):
        """Test that access token contains subject claim."""
        email = "test@example.com"
        data = {"sub": email}
        token = create_access_token(data)

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == email

    def test_verify_access_token_valid(self, test_user_data):
        """Test verifying valid access token."""
        token = create_access_token(data={"sub": test_user_data["email"]})

        payload = verify_token(token)
        assert payload["sub"] == test_user_data["email"]

    def test_verify_access_token_invalid(self):
        """Test verifying invalid token raises HTTPException."""
        invalid_token = "invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            verify_token(invalid_token)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in exc_info.value.detail

    def test_verify_access_token_expired(self, test_user_expired_token):
        """Test verifying expired token raises HTTPException."""
        with pytest.raises(HTTPException) as exc_info:
            verify_token(test_user_expired_token)

        assert exc_info.value.status_code == 401

    def test_verify_access_token_wrong_signature(self, test_user_data):
        """Test verifying token with wrong signature raises HTTPException."""
        # Create token with same algorithm but different secret
        to_encode = {"sub": test_user_data["email"]}
        token = jwt.encode(
            to_encode,
            "wrong-secret-key-that-is-long-enough-123",
            algorithm=settings.ALGORITHM
        )

        with pytest.raises(HTTPException):
            verify_token(token)


class TestRefreshToken:
    """Tests for refresh token creation."""

    def test_create_refresh_token(self):
        """Test creating refresh token."""
        data = {"sub": "test@example.com"}
        token = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_refresh_token_contains_subject(self):
        """Test that refresh token contains subject claim."""
        email = "test@example.com"
        data = {"sub": email}
        token = create_refresh_token(data)

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        assert payload["sub"] == email

    def test_refresh_token_expiration_longer_than_access(self):
        """Test that refresh token expires later than access token."""
        data = {"sub": "test@example.com"}

        access_token = create_access_token(data)
        refresh_token = create_refresh_token(data)

        access_payload = jwt.decode(
            access_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        refresh_payload = jwt.decode(
            refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Refresh token should expire later
        assert refresh_payload["exp"] > access_payload["exp"]

    def test_refresh_token_can_be_verified(self, test_user_data):
        """Test that refresh token can be verified with verify_token."""
        token = create_refresh_token(data={"sub": test_user_data["email"]})

        payload = verify_token(token)
        assert payload["sub"] == test_user_data["email"]
