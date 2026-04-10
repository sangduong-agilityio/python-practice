"""
Project model.

ondelete="CASCADE" on the FK means the database handles cleanup
when a user is deleted, so we do not rely on SQLAlchemy cascade alone.
Both layers agree, which is safer.
"""

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    owner: Mapped["User"] = relationship("User", back_populates="owned_projects")  # type: ignore[name-defined]
    tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]
        "Task",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Project {self.title!r}>"
