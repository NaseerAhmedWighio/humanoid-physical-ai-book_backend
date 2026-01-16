from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserPreferenceBase(BaseModel):
    user_id: str
    hardware_preference: str = Field(..., pattern="^(mobile|laptop|physical_robot)$")
    personalization_enabled: bool = True


class UserPreferenceCreate(UserPreferenceBase):
    pass


class UserPreferenceUpdate(BaseModel):
    hardware_preference: Optional[str] = Field(None, pattern="^(mobile|laptop|physical_robot)$")
    personalization_enabled: Optional[bool] = None


class UserPreference(UserPreferenceBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True