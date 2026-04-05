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


class CaseDetailedResponse(CaseBase):
    """Detailed case response for My Cases portal"""
    id: int
    user_id: int
    lawyer_id: Optional[int] = None
    status: str
    priority: str
    case_number: str
    category: str
    description: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Lawyer information
    lawyer_name: Optional[str] = None
    lawyer_email: Optional[str] = None
    lawyer_phone: Optional[str] = None
    lawyer_specialization: Optional[str] = None

    # Court information
    court_name: Optional[str] = None

    # Statistics
    documents_count: int = 0
    updates_count: int = 0

    # Legal fees
    legal_fees_amount: Optional[float] = None
    legal_fees_paid: Optional[float] = None

    class Config:
        from_attributes = True


class LawyerSimpleResponse(BaseModel):
    """Simple lawyer info for case responses"""
    id: Optional[int] = None
    user_id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None

    class Config:
        from_attributes = True


class CaseDetailedListItemResponse(BaseModel):
    """Single case in detailed list response"""
    id: int
    user_id: int
    lawyer_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    status: str
    priority: Optional[str] = None
    case_number: Optional[str] = None
    court_name: Optional[str] = None
    hearing_date: Optional[datetime] = None
    estimated_completion_date: Optional[datetime] = None
    case_progress: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    lawyer: Optional[LawyerSimpleResponse] = None
    documents_count: int = 0
    updates_count: int = 0
    legal_fees_amount: Optional[float] = None
    legal_fees_paid: Optional[float] = None

    class Config:
        from_attributes = True


class CaseDetailedListResponse(BaseModel):
    """Detailed cases list response for My Cases portal"""
    total: int
    page: int
    cases: list[CaseDetailedListItemResponse]

    class Config:
        from_attributes = True


class CaseStatsResponse(BaseModel):
    """Case statistics response"""
    total_cases: int
    active_cases: int
    pending_cases: int
    closed_cases: int
    resolved_cases: int

    class Config:
        from_attributes = True
