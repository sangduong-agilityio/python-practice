from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    # sub is the JWT "subject" claim -- we store the user UUID here.
    sub: str | None = None
