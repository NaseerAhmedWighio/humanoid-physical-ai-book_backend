from sqlalchemy import Column, Integer, String, Text, Float, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import uuid
from src.database import Base

class CourseModule(Base):
    __tablename__ = "course_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    module_number = Column(Integer, nullable=False)  # 1-4
    description = Column(Text, nullable=False)
    word_count = Column(Integer, nullable=False)  # 3000-5000
    estimated_duration_hours = Column(Float, nullable=False)
    learning_outcomes = Column(JSON, nullable=False)  # JSON Array
    prerequisites = Column(JSON)  # Array of UUIDs (Optional)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())