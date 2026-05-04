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


@router.patch("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, current_user: CurrentUser, db: DbSession) -> UserResponse:
    """Update the current user's profile.

    Only user-editable fields can be updated (e.g. username and/or email).
    System fields (id, created_at, is_active, hashed_password) cannot be modified via this endpoint.

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


@router.get("", response_model=list[UserResponse])
async def list_users(current_user: CurrentUser, db: DbSession, exclude_current: bool = True) -> list[UserResponse]:
    """List all active users for chat feature.

    Args:
        current_user: Authenticated user from JWT token validation.
        db: Database session dependency.
        exclude_current: If True (default), exclude the current user from results.

    Returns:
        List of UserResponse objects (does not include password hashes or sensitive data).
    """
    users = await UserService(db).list_users_for_chat(
        exclude_user_id=current_user.id if exclude_current else None
    )
    return users
