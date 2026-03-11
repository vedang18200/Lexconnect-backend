"""Message schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DirectMessageCreate(BaseModel):
    """Create direct message schema"""
    receiver_id: int
    message: str

class DirectMessageResponse(BaseModel):
    """Direct message response schema"""
    id: int
    sender_id: int
    receiver_id: int
    message: str
    sent_at: datetime
    read_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ChatMessageCreate(BaseModel):
    """Create chat message schema"""
    message: str
    language: Optional[str] = "en"

class ChatMessageResponse(BaseModel):
    """Chat message response schema"""
    id: int
    user_id: int
    message: str
    response: Optional[str] = None
    language: str
    created_at: datetime

    class Config:
        from_attributes = True
