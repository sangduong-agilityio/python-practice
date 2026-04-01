import hashlib
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from bcrypt import hashpw, gensalt, checkpw

from .config import settings

# Password Hashing using bcrypt directly


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    salt = gensalt()
    hashed = hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash"""
    return checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def hash_token(token: str) -> str:
    """Hash a token string using SHA-256 for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# JWT Token Handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenError(Exception):
    """Raised when a JWT token is invalid or expired."""

    pass


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()

    expire = datetime.now() + (
        expires_delta
        if expires_delta
        else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    to_encode.update({
        "exp": expire,
        "sub": str(data.get("sub")),
        "token_type": "access",
    })

    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

# For refresh tokens, we return both the token string and its expiration time


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    """Create a refresh token JWT and return (token_string, expires_at).

    The expires_at datetime is returned so the caller can persist it in the DB
    without re-decoding the token.
    """
    to_encode = data.copy()
    expire = datetime.now() + (
        expires_delta if expires_delta else timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({
        "exp": expire,
        "sub": str(data.get("sub")),
        "token_type": "refresh",
    })
    token = jwt.encode(to_encode, settings.SECRET_KEY,
                       algorithm=settings.ALGORITHM)
    return token, expire


def verify_token(token: str) -> dict:
    """Decode and verify a JWT token.

    Returns:
        The decoded payload dict.

    Raises:
        TokenError: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload
    except JWTError as exc:
        raise TokenError("Invalid or expired token") from exc
