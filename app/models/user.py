"""
User model.

UUID primary keys are preferred over auto-increment integers because
they do not leak row counts and are safe to expose in URLs.
"""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    owned_projects: Mapped[list["Project"]] = relationship(  # type: ignore[name-defined]
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]
        "Task",
        back_populates="assignee",
        foreign_keys="Task.assignee_id",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"
