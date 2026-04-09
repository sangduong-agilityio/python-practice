"""
Re-export every model so alembic/env.py can do a single import
and still see all tables when generating migrations.
"""

from app.models.base import Base, TimestampMixin
from app.models.project import Project
from app.models.tag import Tag
from app.models.task import Task, TaskPriority, TaskStatus, task_tags
from app.models.user import User

__all__ = [
    "Base",
    "TimestampMixin",
    "User",
    "Project",
    "Task",
    "TaskStatus",
    "TaskPriority",
    "task_tags",
    "Tag",
]
