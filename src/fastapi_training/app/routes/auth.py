from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict

from ..schemas.user import UserCreate, UserResponse
from ..services.user_service import authenticate_user, create_user
from ..core.security import create_access_token, create_refresh_token, verify_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate) -> UserResponse:
    """
    
    Register a new user account.

    Args:
        user_in: User registration data (email, password, full_name)

    Returns:
        UserResponse: Created user info
    """
    user = create_user(user_in)
    return UserResponse(
        id=user["id"],
        email=user["email"]
    )


@router.post("/login", status_code=status.HTTP_200_OK)
def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    """
    User login endpoint - returns access and refresh tokens.

    Args:
        form_data: Username (email) and password

    Returns:
        Dictionary with access_token, refresh_token, and token_type

    Raises:
        HTTPException: 401 if credentials are incorrect
    """
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create both access and refresh tokens
    access_token = create_access_token(data={"sub": user["email"]})
    refresh_token = create_refresh_token(data={"sub": user["email"]})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", status_code=status.HTTP_200_OK)
def refresh(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    """
    Refresh access token using refresh token.

    Args:
        form_data: Refresh token passed in password field

    Returns:
        Dictionary with new access_token and token_type

    Raises:
        HTTPException: 401 if refresh token is invalid or expired
    """
    refresh_token = form_data.password

    # Verify refresh token
    payload = verify_token(refresh_token)
    email = payload.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Generate new access token
    new_access_token = create_access_token(data={"sub": email})

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
