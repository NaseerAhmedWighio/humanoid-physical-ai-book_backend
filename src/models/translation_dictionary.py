from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from ..database import Base


class TranslationDictionary(Base):
    __tablename__ = "translation_dictionary"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    english_word = Column(String, nullable=False, unique=True, index=True)
    urdu_translation = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())