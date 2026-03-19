from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas.user import UserCreate, UserResponse
from ..dependencies.db import get_db
from ..services.user_service import authenticate_user, create_user
from ..core.security import create_access_token, create_refresh_token, verify_token

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    user = await create_user(db, user_in)
    return user

@router.post("/login", status_code=status.HTTP_200_OK)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)) -> Dict[str, str]:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", status_code=status.HTTP_200_OK)
async def refresh(form_data: OAuth2PasswordRequestForm = Depends()) -> Dict[str, str]:
    refresh_token = form_data.password
    payload = verify_token(refresh_token)
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    new_access_token = create_access_token(data={"sub": email})
    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }
