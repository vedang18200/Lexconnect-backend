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
    education: Optional[str] = None
    credentials: Optional[str] = None
    bar_council_id: Optional[str] = None
    availability: Optional[str] = None

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
    education: Optional[str] = None
    credentials: Optional[str] = None
    bar_council_id: Optional[str] = None
    availability: Optional[str] = None

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

class LawyerCardResponse(LawyerBase):
    """Enhanced lawyer card response for lawyer listing"""
    id: int
    user_id: int
    rating: Optional[float] = None
    review_count: int = 0
    verified: bool
    total_cases: int = 0
    total_clients: int = 0
    experience: Optional[int] = None
    location: Optional[str] = None
    availability: str = "Available"  # Available, Busy, etc
    response_time: Optional[str] = None  # "Responds within 2 hours"
    languages: Optional[list[str]] = None
    bio: Optional[str] = None
    specializations: Optional[list[str]] = None
    cases_won: int = 0
    success_rate: Optional[float] = None  # percentage
    effective_rating: Optional[float] = None
    available_via: Optional[list[str]] = None  # ["In-Person", "Video Call", "Phone Call"]
    fee_per_hour: Optional[float] = None
    next_slot_available: Optional[str] = None  # "Today at 4:00 PM"
    top_achievement: Optional[str] = None

    class Config:
        from_attributes = True


class LawyerDetailedProfileResponse(BaseModel):
    """Detailed lawyer profile view (for View Profile page)"""
    id: int
    user_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    experience: Optional[int] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    fee_range: Optional[str] = None
    languages: Optional[list[str]] = None
    rating: Optional[float] = None
    review_count: int = 0
    verified: bool
    total_cases: int = 0
    total_clients: int = 0
    availability: str = "Available"

    # Profile details
    specializations: Optional[list[str]] = None
    education: Optional[list[str]] = None  # List of education entries
    credentials: Optional[str] = None  # Bar council and other credentials
    bar_council_id: Optional[str] = None

    # Statistics
    cases_won: int = 0
    success_rate: Optional[float] = None
    effective_rating: Optional[float] = None
    clients_satisfied: int = 0

    # Reviews data
    reviews_summary: Optional[dict] = None  # Contains rating distribution, avg rating, etc

    # Tabs/Sections
    overview_data: Optional[dict] = None
    reviews_data: Optional[list] = None
    achievements_data: Optional[list] = None

    class Config:
        from_attributes = True
