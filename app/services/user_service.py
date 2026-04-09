"""
User business logic.

Services are the only layer that raise HTTPException. Repositories return
None on miss; services decide what that means in context (404, 401, etc.).
"""

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserUpdate
from app.services.email_service import send_welcome


async def register(
    db: AsyncSession,
    data: UserCreate,
    background_tasks: BackgroundTasks,
) -> User:
    """Register a new user and dispatch a welcome email.

    Validates that the requested email and username are not already in use.
    The raw password is automatically hashed before saving to the database.

    Args:
        db: Database session.
        data: Validation schema containing email, username, and plain password.
        background_tasks: FastAPI background task manager for email dispatcher.

    Returns:
        The newly created User instance.

    Raises:
        HTTPException 409: If the email or username is already registered.
    """
    if await user_repository.get_by_email(db, data.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    if await user_repository.get_by_username(db, data.username):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    user = await user_repository.create(db, user)
    background_tasks.add_task(send_welcome, user.email, user.username)
    return user


async def login(db: AsyncSession, email: str, password: str) -> Token:
    """Authenticate a user and generate a JWT access token.

    Verifies the email and password combination. Unspecified HTTP 401 errors
    are thrown for both wrong email and wrong password to prevent user
    enumeration attacks.

    Args:
        db: Database session.
        email: The user's registered email address.
        password: The user's plain-text password.

    Returns:
        A Token object containing the JWT string.

    Raises:
        HTTPException 401: Invalid credentials.
        HTTPException 403: Account exists but is marked inactive.
    """
    user = await user_repository.get_by_email(db, email)

    # Use the same error message whether the email doesn't exist or the
    # password is wrong -- leaking which one is a user-enumeration risk.
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


async def update_profile(db: AsyncSession, user: User, data: UserUpdate) -> User:
    """Update an existing user's profile information.

    Checks for uniqueness constraint violations before updating the database
    if the user is attempting to change their email or username.

    Args:
        db: Database session.
        user: The current authenticated User instance.
        data: UserUpdate schema with optional fields.

    Returns:
        The updated User instance.

    Raises:
        HTTPException 409: If the new email or username is taken by someone else.
    """
    updates = data.model_dump(exclude_none=True)

    if "email" in updates:
        existing = await user_repository.get_by_email(db, updates["email"])
        if existing and existing.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    if "username" in updates:
        existing = await user_repository.get_by_username(db, updates["username"])
        if existing and existing.id != user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    return await user_repository.update(db, user, updates)
