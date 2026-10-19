"""
app/models/project.py
---------------------
SQLAlchemy ORM model for the `projects` table.

Each project belongs to exactly one user (owner) via a ForeignKey.
A project can contain many tasks (one-to-many relationship).
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Project(Base):
    """
    Represents a project that groups related tasks together.

    Columns:
        id          : Auto-incrementing primary key.
        title       : Short name for the project.
        description : Optional longer explanation.
        owner_id    : FK to users.id — who owns/created this project.
        created_at  : Set automatically on INSERT.
        updated_at  : Updated automatically on UPDATE.
    """

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ForeignKey("users.id") references the `id` column of the `users` table.
    # ondelete="CASCADE" means: when the user is deleted, delete their projects too.
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- Relationships ---
    owner: Mapped["User"] = relationship("User", back_populates="projects")  # type: ignore[name-defined]
    tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]
        "Task", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} title={self.title!r}>"
