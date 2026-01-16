from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from src.database import Base

class StudentProgress(Base):
    __tablename__ = "student_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True))  # Store user ID without foreign key constraint
    module_id = Column(UUID(as_uuid=True), ForeignKey("course_modules.id"))  # Foreign Key to CourseModule
    week_id = Column(UUID(as_uuid=True), ForeignKey("weekly_content.id"), nullable=True)  # Foreign Key to WeeklyContent, Optional
    exercise_id = Column(UUID(as_uuid=True), ForeignKey("exercises.id"), nullable=True)  # Foreign Key to Exercise, Optional
    status = Column(String, nullable=False)  # "not_started", "in_progress", "completed"
    score = Column(Float, nullable=True)  # Optional, 0.0-100.0
    attempts_count = Column(Integer, default=0)  # Default: 0
    last_accessed = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())