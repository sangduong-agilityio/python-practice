"""
User business logic.

Services are the only layer that raise HTTPException. Repositories return
None on miss; services decide what that means in context (404, 401, etc.).
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserUpdate
from app.worker.tasks import send_welcome_email


class UserService:
    """Handles user-related business operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = UserRepository(db)

    async def register(self, data: UserCreate) -> User:
        """Register a new user and dispatch a welcome email via Celery."""
        if await self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        if await self.repo.get_by_username(data.username):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
        )
        user = await self.repo.create(user)

        # Fire-and-forget via Celery
        send_welcome_email.delay(user.email, user.username)

        return user

    async def login(self, email: str, password: str) -> Token:
        """Authenticate a user and generate a JWT access token."""
        user = await self.repo.get_by_email(email)

        bad_credentials = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if user is None or not verify_password(password, user.hashed_password):
            raise bad_credentials

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

        return Token(access_token=create_access_token(str(user.id)))

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        """Update an existing user's profile information."""
        updates = data.model_dump(exclude_none=True)

        if "email" in updates:
            existing = await self.repo.get_by_email(updates["email"])
            if existing and existing.id != user.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

        if "username" in updates:
            existing = await self.repo.get_by_username(updates["username"])
            if existing and existing.id != user.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

        return await self.repo.update(user, updates)
