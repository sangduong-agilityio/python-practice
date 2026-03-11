from pydantic import BaseModel
from typing import Optional, List
from .task import TaskResponse


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    user_id: int
    tasks: List[TaskResponse] = []

    class Config:
        from_attributes = True


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class AssignTaskToProjectRequest(BaseModel):
    task_id: int
