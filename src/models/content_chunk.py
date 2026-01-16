from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import uuid
from src.database import Base

class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_id = Column(UUID(as_uuid=True), ForeignKey("course_modules.id"))  # Foreign Key to CourseModule
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)  # Chunk of MD content
    embedding_vector = Column(JSON, nullable=False)  # For vector search
    semantic_tags = Column(JSON)  # Optional, for search optimization
    created_at = Column(DateTime(timezone=True), server_default=func.now())