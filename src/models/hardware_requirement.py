from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import uuid
from src.database import Base

class HardwareRequirement(Base):
    __tablename__ = "hardware_requirements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # "workstation", "edge_computing", "robot_hardware"
    specifications = Column(JSON, nullable=False)  # Required
    recommended_use = Column(Text, nullable=True)
    cost_estimate = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())