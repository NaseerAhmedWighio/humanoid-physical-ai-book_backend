from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import uuid
from src.database import Base

class WeeklyContent(Base):
    __tablename__ = "weekly_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    week_number = Column(Integer, nullable=False)  # 1-13
    title = Column(String, nullable=False)
    module_id = Column(UUID(as_uuid=True), ForeignKey("course_modules.id"))  # Foreign Key to CourseModule
    subtopics = Column(JSON, nullable=False)  # JSON Array
    content_path = Column(String, nullable=False)  # Path to MD file
    exercises_count = Column(Integer, nullable=False)
    quizzes_count = Column(Integer, nullable=False)
    case_studies_count = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())