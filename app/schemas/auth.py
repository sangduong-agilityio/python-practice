"""
Auth-related Pydantic schemas.

Keeping these thin -- they only describe the shape of request/response
payloads and carry no business logic.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """Response schema returned after a successful login or token refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    # sub is the JWT "subject" claim -- we store the user id here.
    sub: str | None = None


class RefreshRequest(BaseModel):
    """Request body for POST /auth/refresh."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Request body for POST /auth/logout.

    ``refresh_token`` is optional: if provided the specific session row is
    revoked in the database; if omitted only the access token is blacklisted.
    Sending the refresh token is strongly recommended so the client cannot
    obtain a new access token after logging out.
    """

    refresh_token: str | None = None
