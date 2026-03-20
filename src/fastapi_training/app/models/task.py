from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..db.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, default="pending")
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)

    # Relationships - lazy="selectin" required for Async SQLAlchemy
    owner = relationship("User", foreign_keys=[user_id], lazy="selectin")
    project = relationship("Project", back_populates="tasks", lazy="selectin")
