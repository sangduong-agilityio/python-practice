"""
Unit tests for app.core.security.

Tests cover pure password hashing and JWT token utilities without
any database or HTTP layer involvement — each test runs in microseconds.
"""

import time
from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    get_access_token_remaining_seconds,
    hash_password,
    hash_token,
    verify_password,
)


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------


def test_hash_password_returns_non_empty_string():
    """hash_password must return a non-empty string."""
    result = hash_password("mypassword")
    assert isinstance(result, str)
    assert len(result) > 0


def test_hash_password_not_plain_text():
    """Hashed value must never equal the original plain-text password."""
    plain = "secret123"
    assert hash_password(plain) != plain


def test_hash_password_is_not_deterministic():
    """Two hashes of the same password must differ (salted hashing)."""
    h1 = hash_password("same_password")
    h2 = hash_password("same_password")
    assert h1 != h2


def test_verify_password_correct():
    """verify_password must return True when password matches the hash."""
    plain = "correct_password"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_wrong():
    """verify_password must return False for wrong passwords."""
    hashed = hash_password("correct_password")
    assert verify_password("wrong_password", hashed) is False


# ---------------------------------------------------------------------------
# JWT access token creation and decoding
# ---------------------------------------------------------------------------


def test_create_access_token_returns_string():
    """create_access_token must produce a non-empty string token."""
    token = create_access_token("42")
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_access_token_returns_subject():
    """decode_access_token must return the subject embedded in the token."""
    token = create_access_token("99")
    subject = decode_access_token(token)
    assert subject == "99"


def test_decode_access_token_invalid_returns_none():
    """decode_access_token returns None for tampered/invalid tokens."""
    assert decode_access_token("not.a.valid.token") is None


def test_decode_access_token_wrong_type_returns_none():
    """Token with typ != 'access' should be rejected."""
    # Manually craft a token without the 'access' typ claim
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    bad_payload = {"sub": "1", "exp": expire, "typ": "refresh"}
    bad_token = jwt.encode(bad_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert decode_access_token(bad_token) is None


def test_decode_access_token_expired_returns_none():
    """Expired tokens must not decode successfully."""
    expire = datetime.now(timezone.utc) - timedelta(seconds=1)
    payload = {"sub": "1", "exp": expire, "typ": "access"}
    expired_token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    assert decode_access_token(expired_token) is None


# ---------------------------------------------------------------------------
# Token remaining seconds
# ---------------------------------------------------------------------------


def test_get_access_token_remaining_seconds_positive():
    """Freshly created token must have positive remaining seconds."""
    token = create_access_token("1")
    remaining = get_access_token_remaining_seconds(token)
    assert remaining > 0
    assert remaining <= settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


def test_get_access_token_remaining_seconds_expired():
    """Expired token must return 0 (not negative)."""
    expire = datetime.now(timezone.utc) - timedelta(seconds=10)
    payload = {"sub": "1", "exp": expire, "typ": "access"}
    expired_token = jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    remaining = get_access_token_remaining_seconds(expired_token)
    assert remaining == 0


# ---------------------------------------------------------------------------
# Refresh token helpers
# ---------------------------------------------------------------------------


def test_generate_refresh_token_is_unique():
    """Each generated refresh token must be unique."""
    tokens = {generate_refresh_token() for _ in range(10)}
    assert len(tokens) == 10


def test_generate_refresh_token_is_string():
    """generate_refresh_token must return a URL-safe string."""
    token = generate_refresh_token()
    assert isinstance(token, str)
    assert len(token) > 0


def test_hash_token_is_deterministic():
    """hash_token must produce the same digest for the same input."""
    raw = "some_opaque_token"
    assert hash_token(raw) == hash_token(raw)


def test_hash_token_differs_for_different_inputs():
    """Different tokens must produce different hashes."""
    assert hash_token("token_a") != hash_token("token_b")


def test_hash_token_returns_64_hex_chars():
    """SHA-256 hex digest must be exactly 64 characters."""
    digest = hash_token("any_token")
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)
