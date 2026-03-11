"""Social worker schemas for validation"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime


# ===== AGENCY SCHEMAS =====

class AgencyBase(BaseModel):
    """Base agency schema"""
    name: str
    description: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    contact_person: Optional[str] = None


class AgencyCreate(AgencyBase):
    """Create agency schema"""
    pass


class AgencyResponse(AgencyBase):
    """Agency response schema"""
    id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== SOCIAL WORKER PROFILE SCHEMAS =====

class SocialWorkerProfileBase(BaseModel):
    """Base social worker profile schema"""
    agency_id: int
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    bio: Optional[str] = None


class SocialWorkerProfileCreate(SocialWorkerProfileBase):
    """Create social worker profile schema"""
    pass


class SocialWorkerProfileUpdate(BaseModel):
    """Update social worker profile schema"""
    license_number: Optional[str] = None
    specialization: Optional[str] = None
    bio: Optional[str] = None


class SocialWorkerProfileResponse(SocialWorkerProfileBase):
    """Social worker profile response schema"""
    id: int
    user_id: int
    is_verified: bool
    verified_at: Optional[datetime] = None
    total_referrals: int
    successful_referrals: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== REFERRAL SCHEMAS =====

class ReferralBase(BaseModel):
    """Base referral schema"""
    lawyer_id: int
    citizen_id: int
    referral_reason: Optional[str] = None
    case_category: Optional[str] = None


class ReferralCreate(ReferralBase):
    """Create referral schema"""
    pass


class ReferralUpdate(BaseModel):
    """Update referral schema"""
    status: Optional[str] = None
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None


class ReferralResponse(ReferralBase):
    """Referral response schema"""
    id: int
    social_worker_id: int
    case_id: Optional[int] = None
    status: str
    outcome: Optional[str] = None
    outcome_notes: Optional[str] = None
    referral_date: datetime
    accepted_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ===== DASHBOARD SCHEMAS =====

class ReferralStats(BaseModel):
    """Referral statistics"""
    total_referrals: int
    pending_referrals: int
    accepted_referrals: int
    completed_referrals: int
    successful_rate: float
    avg_days_to_completion: float


class AgencyStats(BaseModel):
    """Agency statistics"""
    total_social_workers: int
    total_referrals: int
    successful_referrals: int
    pending_referrals: int
    success_rate: float


class SocialWorkerDashboardResponse(BaseModel):
    """Social worker dashboard response"""
    stats: ReferralStats
    recent_referrals: List[ReferralResponse]
    pending_referrals: List[ReferralResponse]
    recent_cases: List[dict]
    active_clients: List[dict]


class AgencyDashboardResponse(BaseModel):
    """Agency dashboard response"""
    stats: AgencyStats
    top_performing_workers: List[dict]
    recent_referrals: List[ReferralResponse]
    case_category_breakdown: dict
    lawyer_collaboration_stats: dict
