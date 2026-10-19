"""
app/models/__init__.py
----------------------
Re-exports all ORM models so Alembic's env.py can import them
from a single location: `from app.models import *`
"""

from app.models.user import User
from app.models.project import Project
from app.models.task import Task, TaskStatus, TaskPriority
from app.models.tag import Tag, TaskTag

__all__ = ["User", "Project", "Task", "TaskStatus", "TaskPriority", "Tag", "TaskTag"]
