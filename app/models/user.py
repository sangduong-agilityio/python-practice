"""
app/models/user.py
------------------
SQLAlchemy ORM model for the `users` table.

A model class maps directly to a database table. Each class attribute
that uses `mapped_column()` becomes a column in that table.
`relationship()` defines how this model connects to other models (ORM-level join).
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    """
    Represents a registered user of the application.

    Columns:
        id            : Auto-incrementing primary key.
        email         : Unique email address used for login.
        username      : Unique display name.
        hashed_password: bcrypt hash — the plain password is NEVER stored.
        is_active     : False = soft-deleted / banned user.
        created_at    : Set automatically on INSERT by the DB server.
        updated_at    : Updated automatically on every UPDATE.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # server_default=func.now() means the DB sets the value, not Python.
    # This is more reliable in distributed / multi-process environments.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),  # Automatically updated on every row update
        nullable=False,
    )

    # --- Relationships (ORM-level, not DB columns) ---
    # back_populates keeps both sides of the relationship in sync in memory.
    projects: Mapped[list["Project"]] = relationship(  # type: ignore[name-defined]
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]
        "Task", back_populates="assignee", foreign_keys="Task.assignee_id"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
