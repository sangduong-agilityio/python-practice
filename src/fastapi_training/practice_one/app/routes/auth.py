from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from ..services.user_service import authenticate_user
from ..core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/token", status_code=status.HTTP_200_OK)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["email"]}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
