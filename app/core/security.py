"""
Password hashing and JWT utilities.

These functions know nothing about HTTP -- no Request, no Response,
no HTTPException. Keeping them pure makes them easy to unit test and
reuse outside the web layer if needed.
"""

from datetime import datetime, timedelta, timezone

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
    settings. The ``sub`` claim stores an opaque string identifier (typically
    a stringified UUID) so we never embed PII directly in the token.

    Args:
        subject: An opaque identifier to embed as the JWT ``sub`` claim.
                 Callers typically pass ``str(user.id)``.

    Returns:
        A compact, URL-safe JWT string signed with HMAC-SHA256.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> str | None:
    """
    Returns the subject claim from a valid token, or None if the token
    is expired, tampered with, or otherwise invalid. The caller decides
    what to do with None -- usually raise a 401.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY,
                             algorithms=[settings.ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
