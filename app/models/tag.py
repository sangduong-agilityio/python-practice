"""
Tag model.

Tags are global -- not scoped to a user or project. Any task can carry
any tag. The color column stores a hex code used by the frontend.
"""

import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.task import task_tags


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#6366f1", nullable=False)

    tasks: Mapped[list["Task"]] = relationship(  # type: ignore[name-defined]
        "Task",
        secondary=task_tags,
        back_populates="tags",
    )

    def __repr__(self) -> str:
        return f"<Tag {self.name!r}>"
