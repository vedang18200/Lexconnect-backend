"""Lawyer professional features schemas"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class LawyerCredentialBase(BaseModel):
    """Base lawyer credential schema"""
    license_number: str
    license_state: Optional[str] = None
    bar_association: Optional[str] = None
    bar_admission_year: Optional[int] = None
    qualifications: Optional[str] = None  # JSON string
    court_admissions: Optional[str] = None  # JSON string


class LawyerCredentialCreate(LawyerCredentialBase):
    """Lawyer credential creation schema"""
    pass


class LawyerCredentialResponse(LawyerCredentialBase):
    """Lawyer credential response schema"""
    id: int
    lawyer_id: int
    is_verified: bool
    verified_at: Optional[datetime] = None
    verification_documents: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LawyerAvailabilityBase(BaseModel):
    """Base availability schema"""
    day_of_week: Optional[int] = None  # 0-6
    start_time: Optional[str] = None  # HH:MM
    end_time: Optional[str] = None  # HH:MM
    is_available: bool = True
    slot_duration_minutes: int = 60
    break_start: Optional[str] = None
    break_end: Optional[str] = None


class LawyerAvailabilityCreate(LawyerAvailabilityBase):
    """Availability creation schema"""
    pass


class LawyerAvailabilityResponse(LawyerAvailabilityBase):
    """Availability response schema"""
    id: int
    lawyer_id: int
    date_specific: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InvoiceBase(BaseModel):
    """Base invoice schema"""
    amount: Decimal
    tax_percentage: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    total_amount: Decimal
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class InvoiceCreate(InvoiceBase):
    """Invoice creation schema"""
    citizen_id: int
    case_id: Optional[int] = None
    consultation_id: Optional[int] = None


class InvoiceResponse(InvoiceBase):
    """Invoice response schema"""
    id: int
    lawyer_id: int
    citizen_id: int
    case_id: Optional[int] = None
    consultation_id: Optional[int] = None
    invoice_number: str
    status: str
    issued_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentTemplateBase(BaseModel):
    """Base document template schema"""
    name: str
    description: Optional[str] = None
    template_type: str
    content: str
    is_public: bool = False
    category: Optional[str] = None
    tags: Optional[str] = None


class DocumentTemplateCreate(DocumentTemplateBase):
    """Template creation schema"""
    pass


class DocumentTemplateResponse(DocumentTemplateBase):
    """Template response schema"""
    id: int
    lawyer_id: int
    usage_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class CaseNoteBase(BaseModel):
    """Base case note schema"""
    note_type: Optional[str] = None
    title: Optional[str] = None
    content: str
    is_private: bool = False
    priority: Optional[str] = None
    due_date: Optional[datetime] = None


class CaseNoteCreate(CaseNoteBase):
    """Case note creation schema"""
    case_id: int


class CaseNoteResponse(CaseNoteBase):
    """Case note response schema"""
    id: int
    case_id: int
    lawyer_id: int
    is_completed: bool
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LawyerDashboardStats(BaseModel):
    """Lawyer dashboard statistics"""
    total_clients: int
    active_cases: int
    completed_cases: int
    total_consultations: int
    upcoming_consultations: int
    total_earned: Decimal
    pending_invoices: int
    unpaid_invoices: Decimal
    avg_satisfaction_rating: float
    total_reviews: int


class LawyerClientSummary(BaseModel):
    """Summary of a client"""
    id: int
    name: str
    email: str
    total_cases: int
    total_spent: Decimal
    last_consultation: Optional[datetime] = None


class LawyerDashboardResponse(BaseModel):
    """Complete lawyer dashboard response"""
    stats: LawyerDashboardStats
    recent_cases: List[dict]
    upcoming_consultations: List[dict]
    active_clients: List[LawyerClientSummary]
    pending_invoices: List[dict]
    recent_reviews: List[dict]
