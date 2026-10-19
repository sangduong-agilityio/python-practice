"""
app/api/v1/endpoints/users.py
------------------------------
User profile endpoints — all require authentication.
"""

from fastapi import APIRouter

from app.core.dependencies import CurrentUser, DbSession
from app.schemas.user import UserOut, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get your own profile",
)
async def get_me(current_user: CurrentUser) -> UserOut:
    """
    Return the profile of the currently authenticated user.

    No DB query needed — the user object was already loaded
    by the `get_current_user` dependency.
    """
    return current_user  # type: ignore[return-value]


@router.put(
    "/me",
    response_model=UserOut,
    summary="Update your profile",
)
async def update_me(
    data: UserUpdate,
    current_user: CurrentUser,
    db: DbSession,
) -> UserOut:
    """
    Update your email, username, or password.

    Only send the fields you want to change — omitted fields are unchanged.
    """
    service = UserService(db)
    updated = await service.update_profile(current_user, data)
    return updated  # type: ignore[return-value]
