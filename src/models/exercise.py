from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from src.database import Base

class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    type = Column(String, nullable=False)  # "coding", "simulation", "conceptual", "quiz"
    difficulty = Column(String, nullable=False)  # "beginner", "intermediate", "advanced"
    content = Column(Text, nullable=False)
    solution = Column(Text, nullable=False)  # Required for auto-graded exercises
    module_id = Column(UUID(as_uuid=True), ForeignKey("course_modules.id"))  # Foreign Key to CourseModule
    week_id = Column(UUID(as_uuid=True), ForeignKey("weekly_content.id"), nullable=True)  # Foreign Key to WeeklyContent, Optional
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())