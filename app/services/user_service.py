"""
app/services/user_service.py
-----------------------------
Business logic for user registration, login, and profile management.

Services sit between route handlers and repositories:
  - Route handlers: validate HTTP input → call service → return HTTP response
  - Services: apply business rules, call repositories, raise HTTPException
  - Repositories: raw DB queries, return ORM objects

This separation keeps each layer focused and testable.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.repositories.user_repository import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, Token


class UserService:
    """Handles all user-related business operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)

    async def register(self, data: UserCreate) -> User:
        """
        Register a new user.

        Business rules:
          - Email must not already be taken.
          - Username must not already be taken.
          - Password is hashed before storage (never stored in plain text).

        Args:
            data: Validated UserCreate schema from the request body.

        Returns:
            The newly created User ORM object.

        Raises:
            HTTPException 400: If email or username is already taken.
        """
        # Check for duplicate email
        if await self.repo.get_by_email(data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An account with this email already exists",
            )

        # Check for duplicate username
        if await self.repo.get_by_username(data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This username is already taken",
            )

        # Hash the password — NEVER store plain text
        hashed = hash_password(data.password)

        return await self.repo.create(
            email=data.email,
            username=data.username,
            hashed_password=hashed,
        )

    async def login(self, email: str, password: str) -> Token:
        """
        Authenticate a user and return a JWT access token.

        Args:
            email    : The email the user typed in.
            password : The plain-text password the user typed in.

        Returns:
            Token schema containing the JWT string.

        Raises:
            HTTPException 401: If credentials are wrong (vague on purpose — security best practice
                               is to NOT tell the user which field was wrong).
        """
        user = await self.repo.get_by_email(email)

        # Use verify_password even if user is None to prevent timing attacks
        # (returning immediately on "user not found" leaks which emails exist)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        # JWT payload — "sub" (subject) is the standard claim for the user identifier
        token = create_access_token(data={"sub": str(user.id)})
        return Token(access_token=token)

    async def update_profile(self, user: User, data: UserUpdate) -> User:
        """
        Update the current user's profile.

        Args:
            user : The authenticated user (from get_current_user dependency).
            data : Fields to update (only non-None fields are changed).

        Returns:
            Updated User object.
        """
        updates: dict = {}

        if data.email is not None:
            # Check the new email isn't already taken by someone else
            existing = await self.repo.get_by_email(data.email)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This email is already in use",
                )
            updates["email"] = data.email.lower()

        if data.username is not None:
            existing = await self.repo.get_by_username(data.username)
            if existing and existing.id != user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="This username is already taken",
                )
            updates["username"] = data.username.lower()

        if data.password is not None:
            updates["hashed_password"] = hash_password(data.password)

        if not updates:
            return user  # Nothing to change

        return await self.repo.update(user, **updates)
