from pydantic import BaseModel


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str


class LogoutRequest(BaseModel):
    """Schema for logout request — client sends the refresh token to revoke."""

    refresh_token: str


class TokenResponse(BaseModel):
    """Schema for token response."""

    access_token: str
    token_type: str = "bearer"


class LoginTokenResponse(TokenResponse):
    """Schema for login response with both tokens."""

    refresh_token: str
