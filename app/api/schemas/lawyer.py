"""Lawyer schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LawyerBase(BaseModel):
    """Base lawyer schema"""
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    experience: Optional[int] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    fee_range: Optional[str] = None
    languages: Optional[str] = None

class LawyerCreate(LawyerBase):
    """Lawyer creation schema"""
    user_id: int

class LawyerUpdate(BaseModel):
    """Lawyer update schema"""
    specialization: Optional[str] = None
    experience: Optional[int] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    fee_range: Optional[str] = None
    languages: Optional[str] = None

class LawyerResponse(LawyerBase):
    """Lawyer response schema"""
    id: int
    user_id: int
    rating: Optional[float] = None
    verified: bool
    total_cases: int
    total_clients: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
