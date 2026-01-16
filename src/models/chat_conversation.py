from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime


class ChatConversationBase(BaseModel):
    user_id: Optional[str] = None
    messages: List[Message] = []


class ChatConversationCreate(ChatConversationBase):
    pass


class ChatConversationUpdate(BaseModel):
    messages: Optional[List[Message]] = None


class ChatConversation(ChatConversationBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True