"""
Password hashing, JWT, and token utilities.

These functions know nothing about HTTP -- no Request, no Response,
no HTTPException. Keeping them pure makes them easy to unit test and
reuse outside the web layer if needed.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Use argon2 (no 72-byte limit like bcrypt)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plain-text password using Argon2.

    Args:
        plain: The raw password string submitted by the user.

    Returns:
        A salted Argon2 hash safe to persist in the database.
    """
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain-text password against its stored hash.

    Args:
        plain: The raw password string to check.
        hashed: The Argon2 hash retrieved from the database.

    Returns:
        True if the password matches the hash, False otherwise.
    """
    return pwd_context.verify(plain, hashed)


def create_access_token(subject: str) -> str:
    """Create a signed JWT access token for the given subject.

    The token lifetime is controlled by ``ACCESS_TOKEN_EXPIRE_MINUTES`` in
    settings.  The ``sub`` claim stores an opaque string identifier (typically
    a stringified integer) so we never embed PII directly in the token.

    Args:
        subject: An opaque identifier to embed as the JWT ``sub`` claim.
                 Callers typically pass ``str(user.id)``.

    Returns:
        A compact, URL-safe JWT string signed with HMAC-SHA256.
    """
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire, "typ": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """Decode a JWT access token and return the ``sub`` claim.

    Returns ``None`` if the token is expired, tampered with, missing the
    ``typ: access`` claim, or otherwise invalid.  The caller decides what to
    do with ``None`` -- usually raise a 401.
    """
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        if payload.get("typ") != "access":
            return None
        return payload.get("sub")
    except JWTError:
        return None


def get_access_token_remaining_seconds(token: str) -> int:
    """Return how many seconds remain until the access token expires.

    Decodes the JWT *without* re-validating the signature (the caller must
    have already validated it).  Returns 0 if expired or the ``exp`` claim
    is missing -- safe to pass directly to Redis SETEX.

    Args:
        token: A raw JWT access token string.

    Returns:
        Remaining lifetime in whole seconds, floored at 0.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False},
        )
        exp = payload.get("exp")
        if exp is None:
            return 0
        remaining = int(exp) - int(datetime.now(UTC).timestamp())
        return max(remaining, 0)
    except JWTError:
        return 0


def generate_refresh_token() -> str:
    """Generate a cryptographically secure random opaque refresh token.

    Uses ``secrets.token_urlsafe`` which draws from the OS CSPRNG
    (``/dev/urandom`` on Linux, ``CryptGenRandom`` on Windows).

    Returns:
        A 86-character URL-safe Base64 string (64 bytes of entropy).
    """
    return secrets.token_urlsafe(64)


def hash_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of a raw token for safe DB storage.

    Only the hash is ever persisted.  To verify an incoming refresh token,
    hash it with this function and compare against the stored digest.

    Args:
        raw_token: The plain-text token string held by the client.

    Returns:
        A 64-character lowercase hex string.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()
