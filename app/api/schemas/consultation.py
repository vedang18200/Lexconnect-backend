"""Consultation schemas"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ConsultationBase(BaseModel):
    """Base consultation schema"""
    consultation_type: Optional[str] = None
    duration_minutes: Optional[int] = None
    fee_amount: Optional[float] = None
    notes: Optional[str] = None

class ConsultationCreate(ConsultationBase):
    """Consultation creation schema"""
    user_id: int
    lawyer_id: int
    scheduled_at: Optional[datetime] = None

class ConsultationUpdate(BaseModel):
    """Consultation update schema"""
    status: Optional[str] = None
    consultation_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    fee_amount: Optional[float] = None
    notes: Optional[str] = None

class ConsultationResponse(ConsultationBase):
    """Consultation response schema"""
    id: int
    user_id: int
    lawyer_id: int
    status: str
    scheduled_at: Optional[datetime] = None
    consultation_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
