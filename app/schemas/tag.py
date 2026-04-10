from pydantic import BaseModel, Field


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    # Validate that color is a valid hex code before it reaches the DB.
    color: str = Field(default="#6366f1", pattern=r"^#[0-9a-fA-F]{6}$")


class TagResponse(BaseModel):
    id: int
    name: str
    color: str

    model_config = {"from_attributes": True}
