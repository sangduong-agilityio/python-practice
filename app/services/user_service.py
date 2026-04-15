"""
User business logic.

Services raise custom domain exceptions (ResourceNotFoundException, PermissionDeniedException, etc).
Repositories return None on miss; services decide what that means in context.
"""
import structlog
from datetime import datetime, timedelta, timezone
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import blacklist_token, is_token_blacklisted
from app.core.config import settings
from app.core.exceptions import InvalidFieldException, PermissionDeniedException, ResourceNotFoundException, ResourceAlreadyExistsException
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_access_token_remaining_seconds,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserUpdate
from app.worker.tasks import send_welcome_email

log = structlog.get_logger(__name__)


class UserService:
    """Handles user-related business operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)
        self.token_repo = RefreshTokenRepository(db)

    async def register(self, data: UserCreate, request_id: str = "unknown") -> User:
        """Register a new user and dispatch a welcome email via Celery."""
        if await self.repo.get_by_email(data.email):
            raise ResourceAlreadyExistsException("Email is already registered")

        if await self.repo.get_by_username(data.username):
            raise ResourceAlreadyExistsException("Username is already taken")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
        )
        user = await self.repo.create(user)

        # Fire-and-forget via Celery
        task = send_welcome_email.delay(user.email, user.username, request_id)
        log.info(
            "background_task_dispatched",
            task_name="send_welcome_email",
            task_id=task.id,
            email=user.email,
            username=user.username,
            request_id=request_id,
        )

        return user

    async def login(
        self,
        email: str,
        password: str,
        request: Request | None = None,
    ) -> Token:
        """Authenticate a user and return a JWT access token + opaque refresh token.

        Args:
            email: The user's email address.
            password: The plain-text password to verify.
            request: Optional FastAPI Request used to capture device / IP info
                     for the refresh token audit row.

        Returns:
            A ``Token`` containing both tokens.

        Raises:
            PermissionDeniedException: Credentials are wrong or account is inactive.
        """
        user = await self.repo.get_by_email(email)

        if user is None or not verify_password(password, user.hashed_password):
            raise PermissionDeniedException("Incorrect email or password")

        if not user.is_active:
            raise PermissionDeniedException("Account is inactive")

        return await self._issue_token_pair(user, request)

    async def refresh(self, raw_refresh_token: str) -> Token:
        """Exchange a valid refresh token for a new access + refresh token pair.

        Args:
            raw_refresh_token: The opaque refresh token string held by the client.

        Returns:
            A new ``Token`` containing a fresh access and refresh token.

        Raises:
            PermissionDeniedException: Token is invalid, expired, revoked, or being reused.
        """
        token_hash = hash_token(raw_refresh_token)
        db_token = await self.token_repo.get_by_hash(token_hash)

        if db_token is None or db_token.is_revoked:
            raise PermissionDeniedException("Invalid or expired refresh token")

        # Check expiry at the application layer.
        expires_at = db_token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at < datetime.now(timezone.utc):
            raise PermissionDeniedException("Invalid or expired refresh token")

        # If ``used_at`` is already set the token was already rotated.
        # Someone (possibly an attacker) is replaying an old refresh token.
        if db_token.used_at is not None:
            log.warning(
                "refresh_token_reuse_detected",
                user_id=db_token.user_id,
                token_id=db_token.id,
            )
            # Revoke ALL sessions for this user to be safe.
            await self.token_repo.revoke_all_for_user(db_token.user_id)
            raise PermissionDeniedException("Invalid or expired refresh token")

        # Load user and confirm still active.
        user = await self.repo.get_by_id(db_token.user_id)
        if user is None or not user.is_active:
            raise PermissionDeniedException("Invalid or expired refresh token")

        # Mark old token as used (rotation -- one-time-use).
        await self.token_repo.mark_used(db_token)

        # Issue a completely new pair.
        return await self._issue_token_pair(user, request=None)

    async def logout(
        self,
        access_token: str,
        raw_refresh_token: str | None = None,
    ) -> None:
        """Revoke the current session.

        Args:
            access_token: The raw Bearer JWT currently in use.
            raw_refresh_token: Optional opaque refresh token to revoke.
        """
        # Blacklist access token.
        remaining = get_access_token_remaining_seconds(access_token)
        if remaining > 0:
            await blacklist_token(access_token, remaining)

        # Revoke the refresh token row in the DB if provided.
        if raw_refresh_token:
            token_hash = hash_token(raw_refresh_token)
            db_token = await self.token_repo.get_by_hash(token_hash)
            if db_token and not db_token.is_revoked:
                await self.token_repo.revoke(db_token)

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        """Update an existing user's profile information."""
        updates = data.model_dump(exclude_none=True)

        if "email" in updates:
            existing = await self.repo.get_by_email(updates["email"])
            if existing and existing.id != user.id:
                raise ResourceAlreadyExistsException("Email is already in use")

        if "username" in updates:
            existing = await self.repo.get_by_username(updates["username"])
            if existing and existing.id != user.id:
                raise ResourceAlreadyExistsException(
                    "Username is already taken")

        try:
            return await self.repo.update(user, updates)
        except ValueError as e:
            raise InvalidFieldException(
                str(e).replace("Cannot update field: ", ""))

    async def _issue_token_pair(
        self,
        user: User,
        request: Request | None,
    ) -> Token:
        """Create a JWT access token and a new opaque refresh token for ``user``.

        Persists the SHA-256 hash of the refresh token to the DB.  The raw
        refresh token is returned to the caller and is never stored elsewhere.

        Args:
            user: The authenticated User ORM instance.
            request: Optional request used to capture device / IP metadata.

        Returns:
            A ``Token`` schema containing both tokens.
        """
        # -- Access token (JWT, stateless) --
        access_token = create_access_token(str(user.id))

        # -- Refresh token (opaque, stored as hash) --
        raw_refresh = generate_refresh_token()
        token_hash = hash_token(raw_refresh)
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        device_info: str | None = None
        ip_address: str | None = None
        if request is not None:
            device_info = request.headers.get("User-Agent", "")[:255]
            ip_address = _get_client_ip(request)

        await self.token_repo.create(
            RefreshToken(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at,
                device_info=device_info,
                ip_address=ip_address,
            )
        )

        return Token(access_token=access_token, refresh_token=raw_refresh)


def _get_client_ip(request: Request) -> str | None:
    """Extract the real client IP, honouring X-Forwarded-For if present."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None
