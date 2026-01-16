from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import uuid
from src.database import Base

class AssessmentProject(Base):
    __tablename__ = "assessment_projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    project_number = Column(Integer, nullable=False)  # 1-4
    description = Column(Text, nullable=False)
    rubric = Column(JSON, nullable=False)  # Required, evaluation criteria
    module_id = Column(UUID(as_uuid=True), ForeignKey("course_modules.id"), nullable=True)  # Foreign Key to CourseModule, Optional
    deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())