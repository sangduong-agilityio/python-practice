"""
Unit tests for security module (JWT and password hashing).
"""
import pytest
from datetime import timedelta
from jose import JWTError, jwt

from src.fastapi_training.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    hash_token,
    TokenError,
)
from src.fastapi_training.core.config import settings


class TestPasswordHashing:
    """Tests for password hashing functions."""

    @pytest.mark.parametrize("password", [
        "MySecurePassword123",
        "AnotherPassword456!@#",
        "VeryLongPasswordWith1234567890Characters",
        "SpecialChar!@#$%^&*()",
    ])
    def test_hash_password(self, password):
        """Test password hashing with various passwords."""
        hashed = hash_password(password)

        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    @pytest.mark.parametrize("password", [
        "MySecurePassword123",
        "AnotherPassword456!@#",
        "VeryLongPasswordWith1234567890Characters",
    ])
    def test_verify_password_correct(self, password):
        """Test password verification with correct password."""
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    @pytest.mark.parametrize("password,wrong_password", [
        ("MySecurePassword123", "WrongPassword123"),
        ("Admin@123", "Admin@124"),
        ("Test1234", "Test5678"),
    ])
    def test_verify_password_incorrect(self, password, wrong_password):
        """Test password verification with wrong password."""
        hashed = hash_password(password)
        assert verify_password(wrong_password, hashed) is False

    @pytest.mark.parametrize("password", [
        "MySecurePassword123",
        "AnotherPassword456!@#",
    ])
    def test_verify_password_empty(self, password):
        """Test password verification with empty password."""
        hashed = hash_password(password)
        assert verify_password("", hashed) is False

    def test_hash_same_password_different_hashes(self):
        """Test that hashing same password produces different hashes (due to salt)."""
        password = "MySecurePassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2, "Same password should produce different hashes due to salt"
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestTokenHashing:
    """Tests for token hashing function."""

    def test_hash_token(self):
        """Test token hashing produces consistently the same SHA-256 string."""
        token = "test.token.string"
        hashed1 = hash_token(token)
        hashed2 = hash_token(token)

        assert hashed1 == hashed2, "Same token must produce same hash"
        assert hashed1 != token
        assert len(hashed1) == 64  # SHA-256 hexdigest length


class TestAccessToken:
    """Tests for access token creation and verification."""

    @pytest.mark.parametrize("email", [
        "test@example.com",
        "user@domain.co.uk",
        "complex.email+tag@subdomain.com",
    ])
    def test_create_access_token(self, email):
        """Test creating access token with various emails."""
        data = {"sub": email}
        token = create_access_token(data)

        assert isinstance(token, str), "Token should be a string"
        assert len(token) > 0, "Token should not be empty"
        assert token.count(".") == 2, "Token should have JWT format with 3 parts"

    @pytest.mark.parametrize("hours", [1, 2, 24])
    def test_create_access_token_with_custom_expiration(self, hours):
        """Test creating access token with different custom expiration times."""
        data = {"sub": "test@example.com"}
        expires_delta = timedelta(hours=hours)
        token = create_access_token(data, expires_delta)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload, "Token should have exp claim"
        assert payload["sub"] == "test@example.com", "Token should contain correct email"

    @pytest.mark.parametrize("email", [
        "test@example.com",
        "user@domain.co.uk",
        "complex.email+tag@subdomain.com",
    ])
    def test_create_access_token_contains_subject(self, email):
        """Test that access token contains subject claim."""
        data = {"sub": email}
        token = create_access_token(data)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == email, "Token should contain correct email in sub claim"

    def test_verify_access_token_valid(self, test_user_data):
        """Test verifying valid access token."""
        token = create_access_token(data={"sub": test_user_data["email"]})
        payload = verify_token(token)

        assert payload["sub"] == test_user_data["email"], "Token should decode to correct email"

    @pytest.mark.parametrize("invalid_token", [
        "invalid.token.here",
        "completely-invalid",
        "too.many.dots.here.now",
        "",
    ])
    def test_verify_access_token_invalid(self, invalid_token):
        """Test verifying invalid tokens raises TokenError (not HTTPException)."""
        with pytest.raises(TokenError) as exc_info:
            verify_token(invalid_token)

        assert "Invalid or expired token" in str(exc_info.value)

    def test_verify_access_token_expired(self, test_user_expired_token):
        """Test verifying expired token raises TokenError."""
        with pytest.raises(TokenError):
            verify_token(test_user_expired_token)

    def test_verify_access_token_wrong_signature(self, test_user_data):
        """Test verifying token with wrong signature raises TokenError."""
        to_encode = {"sub": test_user_data["email"]}
        token = jwt.encode(
            to_encode,
            "wrong-secret-key-that-is-long-enough-123",
            algorithm=settings.ALGORITHM,
        )

        with pytest.raises(TokenError):
            verify_token(token)


class TestRefreshToken:
    """Tests for refresh token creation.

    create_refresh_token now returns a (token_str, expires_at) tuple so callers
    can persist the expiry in the DB without re-decoding the token.
    """

    def test_create_refresh_token(self):
        """Test creating refresh token returns a JWT string and an expiry datetime."""
        from datetime import datetime
        data = {"sub": "test@example.com"}
        token, expires_at = create_refresh_token(data)

        assert isinstance(token, str)
        assert len(token) > 0
        assert isinstance(expires_at, datetime)

    def test_create_refresh_token_contains_subject(self):
        """Test that refresh token contains subject claim."""
        email = "test@example.com"
        data = {"sub": email}
        token, _ = create_refresh_token(data)

        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == email

    def test_refresh_token_expiration_longer_than_access(self):
        """Test that refresh token expires later than access token."""
        data = {"sub": "test@example.com"}

        access_token = create_access_token(data)
        refresh_token, _ = create_refresh_token(data)

        access_payload = jwt.decode(access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        refresh_payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        assert refresh_payload["exp"] > access_payload["exp"]

    def test_refresh_token_can_be_verified(self, test_user_data):
        """Test that refresh token can be verified with verify_token."""
        token, _ = create_refresh_token(data={"sub": test_user_data["email"]})

        payload = verify_token(token)
        assert payload["sub"] == test_user_data["email"]

