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
    """Retrieve the current authenticated user's profile.

    Args:
        current_user: Authenticated user from JWT token validation.

    Returns:
        UserResponse: The current user's profile data.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, current_user: CurrentUser, db: DbSession) -> UserResponse:
    """Update the current user's profile.

    Only the following fields can be updated: username, email, hashed_password, is_active.
    System fields (id, created_at) cannot be modified.

    Args:
        data: User update schema with fields to modify (supports partial updates).
        current_user: Authenticated user from JWT token validation.
        db: Database session dependency.

    Returns:
        UserResponse: The updated user profile.

    Raises:
        ResourceAlreadyExistsException (409): Email or username already in use by another user.
        InvalidFieldException (400): Attempted to update a non-whitelisted field.
    """
    updated = await UserService(db).update_profile(current_user, data)
    return updated
