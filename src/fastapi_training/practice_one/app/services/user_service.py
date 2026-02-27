from fastapi import HTTPException, status
from ..db.fake_db import fake_users_db
from ..core.security import hash_password, verify_password
from ..schemas.user import UserCreate, UserResponse


def create_user(user_in: UserCreate):
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


def authenticate_user(email: str, password: str):
    # Find user by email
    for user in fake_users_db:
        if user["email"] == email:
            if verify_password(password, user["hashed_password"]):
                return user
            return None
    return None
