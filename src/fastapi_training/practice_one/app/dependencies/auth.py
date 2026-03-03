from fastapi import Depends, HTTPException, status
from ..core.security import oauth2_scheme, verify_token
from ..db.fake_db import fake_users_db


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)

    email = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )

    # Find user in fake DB
    for user in fake_users_db:
        if user["email"] == email:
            return user

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="User not found"
    )
