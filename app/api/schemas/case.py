"""Case schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CaseBase(BaseModel):
    """Base case schema"""
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = "medium"
    case_number: Optional[str] = None

class CaseCreate(CaseBase):
    """Case creation schema"""
    user_id: int
    lawyer_id: Optional[int] = None

class CaseUpdate(BaseModel):
    """Case update schema"""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    lawyer_id: Optional[int] = None

class CaseResponse(CaseBase):
    """Case response schema"""
    id: int
    user_id: int
    lawyer_id: Optional[int] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
