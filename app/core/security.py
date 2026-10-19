"""
app/core/security.py
--------------------
Password hashing and JWT (JSON Web Token) utilities.

How JWTs work:
  1. User logs in with correct password.
  2. Server creates a JWT containing the user's ID and an expiry time.
  3. JWT is signed with SECRET_KEY — nobody can tamper with it without the key.
  4. Client sends the JWT in every request header: `Authorization: Bearer <token>`
  5. Server decodes + verifies the JWT to identify the user — no DB lookup needed.
"""

from datetime import UTC, datetime, timedelta

import bcrypt
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Workaround for passlib + bcrypt >= 4.0.0 on Python 3.13
_orig_hashpw = bcrypt.hashpw
bcrypt.hashpw = lambda secret, config: _orig_hashpw(secret[:72], config)

# ---------------------------------------------------------------------------
# Password Hashing
# ---------------------------------------------------------------------------
# CryptContext handles multiple hashing schemes and automatic upgrades.
# "bcrypt" is the recommended scheme — it's intentionally slow to deter brute force.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        plain_password: The raw password from the user's registration form.

    Returns:
        A bcrypt hash string (safe to store in the database).
    """
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Compare a plain-text password against a stored bcrypt hash.

    Args:
        plain_password  : What the user typed into the login form.
        hashed_password : The hash stored in the database.

    Returns:
        True if they match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT Tokens
# ---------------------------------------------------------------------------

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data          : Payload to encode (typically {"sub": str(user_id)}).
        expires_delta : How long the token is valid. Defaults to settings value.

    Returns:
        A signed JWT string to send to the client.
    """
    to_encode = data.copy()

    # Calculate expiry time in UTC
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # "exp" is a standard JWT claim — jose reads it automatically on decode
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    """
    Decode and verify a JWT access token.

    Args:
        token: The raw JWT string from the Authorization header.

    Returns:
        The decoded payload dict, or None if the token is invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        # Invalid signature, expired, or malformed token — treat as unauthenticated
        return None
