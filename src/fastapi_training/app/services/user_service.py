from typing import Optional
from fastapi import HTTPException, status
from ..db.fake_db import fake_users_db
from ..core.security import hash_password, verify_password
from ..schemas.user import UserCreate, UserResponse


def create_user(user_in: UserCreate) -> dict:
    """
    Create a new user account.

    Args:
        user_in: UserCreate schema with email and password

    Returns:
        Dictionary containing newly created user (id, email, hashed_password)

    Raises:
        HTTPException: 400 if email already registered
    """
    # Check if user already exists
    for user in fake_users_db:
        if user["email"] == user_in.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    # Hash the password
    hashed_password = hash_password(user_in.password)

    # Create new user dict
    new_user = {
        "id": len(fake_users_db) + 1,
        "email": user_in.email,
        "hashed_password": hashed_password
    }

    # Save to fake DB
    fake_users_db.append(new_user)

    return new_user


def authenticate_user(email: str, password: str) -> Optional[dict]:
    """
    Authenticate user by email and password.

    Args:
        email: User email address
        password: Plain text password (will be verified against hash)

    Returns:
        User dictionary if credentials are valid, None otherwise
    """
    # Find user by email
    for user in fake_users_db:
        if user["email"] == email:
            if verify_password(password, user["hashed_password"]):
                return user
            return None
    return None


def update_user(user_id: int, user_update) -> Optional[dict]:
    """
    Update user profile information.

    Args:
        user_id: ID of the user to update
        user_update: UserUpdate schema with optional email/password fields

    Returns:
        Updated user dictionary if found, None otherwise
    """
    for user in fake_users_db:
        if user["id"] == user_id:

            if user_update.email is not None:
                user["email"] = user_update.email

            if user_update.password is not None:
                user["hashed_password"] = hash_password(user_update.password)

            return user

    return None
