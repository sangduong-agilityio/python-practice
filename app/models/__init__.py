"""
app/models/__init__.py
----------------------
Re-exports all ORM models so Alembic's env.py can import them
from a single location: `from app.models import *`
"""

from app.models.project import Project
from app.models.tag import Tag, TaskTag
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.task_comment import TaskComment
from app.models.user import User

__all__ = [
    "User",
    "Project",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "Tag",
    "TaskTag",
    "TaskComment",
]
