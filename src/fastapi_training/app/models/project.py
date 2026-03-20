from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..db.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relationships - lazy="selectin" required for Async SQLAlchemy
    owner = relationship("User", foreign_keys=[user_id], lazy="selectin")
    tasks = relationship("Task", back_populates="project", lazy="selectin")
