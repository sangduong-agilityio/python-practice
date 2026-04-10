"""
app/api/v1/endpoints/users.py
------------------------------
User profile endpoints — all require authentication.
"""

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser) -> UserResponse:
    return current_user 


@router.put("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, current_user: CurrentUser, db: DbSession) -> UserResponse:
    updated = await UserService(db).update_profile(current_user, data)
    return updated 
