from fastapi import APIRouter
from ..schemas.user import UserCreate, UserResponse
from ..services.user_service import create_user

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(user_in: UserCreate):
    user = create_user(user_in)
    return UserResponse(
        id=user["id"],
        email=user["email"]
    )
