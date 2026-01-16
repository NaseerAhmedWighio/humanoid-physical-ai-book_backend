from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PersonalizedContentBase(BaseModel):
    original_content_id: str
    user_id: str
    hardware_preference: str = Field(..., pattern="^(mobile|laptop|physical_robot)$")
    personalized_content: str


class PersonalizedContentCreate(PersonalizedContentBase):
    pass


class PersonalizedContentUpdate(BaseModel):
    personalized_content: Optional[str] = None
    hardware_preference: Optional[str] = Field(None, pattern="^(mobile|laptop|physical_robot)$")


class PersonalizedContent(PersonalizedContentBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True