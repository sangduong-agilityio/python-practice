from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..db.database import Base
from ..schemas.task import TaskStatus

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, default=TaskStatus.PENDING.value)
    user_id = Column(Integer, ForeignKey("users.id"))
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    
    # Relationships
    owner = relationship("User", foreign_keys=[user_id])
    project = relationship("Project", back_populates="tasks")
