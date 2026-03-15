"""Citizen profile and related schemas"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class CitizenProfileBase(BaseModel):
    """Base citizen profile schema"""
    full_name: Optional[str] = None
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    bio: Optional[str] = None
    profile_picture_url: Optional[str] = None


class CitizenProfileCreate(CitizenProfileBase):
    """Citizen profile creation schema"""
    pass


class CitizenProfileUpdate(CitizenProfileBase):
    """Citizen profile update schema"""
    pass


class CitizenProfileResponse(CitizenProfileBase):
    """Citizen profile response schema"""
    id: int
    user_id: int
    is_kyc_verified: bool
    kyc_verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DocumentUploadBase(BaseModel):
    """Base document upload schema"""
    document_type: Optional[str] = None
    file_name: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    description: Optional[str] = None


class DocumentUploadCreate(DocumentUploadBase):
    """Document upload creation schema"""
    case_id: Optional[int] = None


class DocumentUploadResponse(DocumentUploadBase):
    """Document upload response schema"""
    id: int
    user_id: int
    case_id: Optional[int] = None
    file_url: str
    is_verified: bool
    uploaded_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LawyerReviewBase(BaseModel):
    """Base lawyer review schema"""
    rating: int  # 1-5
    title: Optional[str] = None
    review_text: Optional[str] = None
    communication_rating: Optional[int] = None  # 1-5
    professionalism_rating: Optional[int] = None  # 1-5
    effectiveness_rating: Optional[int] = None  # 1-5


class LawyerReviewCreate(LawyerReviewBase):
    """Lawyer review creation schema"""
    lawyer_id: int
    case_id: Optional[int] = None


class LawyerReviewResponse(LawyerReviewBase):
    """Lawyer review response schema"""
    id: int
    lawyer_id: int
    citizen_id: int
    case_id: Optional[int] = None
    is_verified_client: bool
    helpful_count: int
    unhelpful_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaymentBase(BaseModel):
    """Base payment schema"""
    amount: Decimal
    payment_method: str
    description: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Payment creation schema"""
    lawyer_id: int
    consultation_id: Optional[int] = None
    case_id: Optional[int] = None


class PaymentResponse(PaymentBase):
    """Payment response schema"""
    id: int
    citizen_id: int
    lawyer_id: int
    consultation_id: Optional[int] = None
    case_id: Optional[int] = None
    status: str
    transaction_id: Optional[str] = None
    paid_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TwoFactorAuthBase(BaseModel):
    """Base 2FA schema"""
    auth_method: Optional[str] = None
    phone_number: Optional[str] = None


class TwoFactorAuthSetup(BaseModel):
    """2FA setup request schema"""
    auth_method: str  # sms, email, totp
    phone_number: Optional[str] = None


class TwoFactorAuthVerify(BaseModel):
    """2FA verification schema"""
    code: str


class TwoFactorAuthResponse(TwoFactorAuthBase):
    """2FA response schema"""
    id: int
    user_id: int
    is_enabled: bool
    verified_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotificationBase(BaseModel):
    """Base notification schema"""
    notification_type: str
    title: str
    message: str
    related_id: Optional[int] = None


class NotificationResponse(NotificationBase):
    """Notification response schema"""
    id: int
    user_id: int
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Dashboard statistics schema"""
    total_cases: int
    active_cases: int
    resolved_cases: int
    total_consultations: int
    upcoming_consultations: int
    total_spent: Decimal
    pending_payments: int
    unread_notifications: int



# --- Case summary for dashboard ---
from datetime import date

class CaseSummaryItem(BaseModel):
    id: int
    title: str
    lawyer: str
    status: str
    nextHearing: date | None = None
    description: str | None = None
