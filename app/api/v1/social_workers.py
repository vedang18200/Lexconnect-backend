"""Social worker endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.core.security import verify_token
from fastapi.security import HTTPAuthorizationCredentials
from app.services.social_worker_service import (
    SocialWorkerProfileService, ReferralService, SocialWorkerDashboardService
)
from app.api.schemas.social_worker import (
    SocialWorkerProfileResponse, SocialWorkerProfileCreate, SocialWorkerProfileUpdate,
    ReferralResponse, ReferralCreate, ReferralUpdate,
    AgencyResponse, SocialWorkerDashboardResponse, AgencyDashboardResponse
)
from typing import List, Optional

router = APIRouter(prefix="/social-workers", tags=["Social Workers"])


# ===== PROFILE ENDPOINTS =====

@router.post("/profile", response_model=SocialWorkerProfileResponse)
def create_or_get_profile(
    profile: SocialWorkerProfileCreate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create or get social worker profile"""
    user_id = int(credentials.get("sub"))
    db_profile = SocialWorkerProfileService.get_or_create_profile(db, user_id, profile)
    return db_profile


@router.get("/profile", response_model=SocialWorkerProfileResponse)
def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get social worker profile"""
    user_id = int(credentials.get("sub"))
    profile = SocialWorkerProfileService.get_profile(db, user_id)
    return profile


@router.put("/profile", response_model=SocialWorkerProfileResponse)
def update_profile(
    update_data: SocialWorkerProfileUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update social worker profile"""
    user_id = int(credentials.get("sub"))
    profile = SocialWorkerProfileService.update_profile(
        db, user_id, update_data.dict(exclude_unset=True)
    )
    return profile


# ===== REFERRAL ENDPOINTS =====

@router.post("/referrals", response_model=ReferralResponse)
def create_referral(
    referral: ReferralCreate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create a referral"""
    user_id = int(credentials.get("sub"))
    db_referral = ReferralService.create_referral(db, user_id, referral)
    return db_referral


@router.get("/referrals", response_model=dict)
def list_referrals(
    skip: int = Query(0),
    limit: int = Query(10),
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List referrals created by social worker"""
    user_id = int(credentials.get("sub"))
    if status:
        return ReferralService.get_referrals_by_status(db, user_id, status, skip, limit)
    else:
        return ReferralService.get_social_worker_referrals(db, user_id, skip, limit)


@router.get("/referrals/{referral_id}", response_model=ReferralResponse)
def get_referral(
    referral_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get referral details"""
    user_id = int(credentials.get("sub"))
    referral = ReferralService.get_referral(db, referral_id, user_id)
    return referral


@router.put("/referrals/{referral_id}", response_model=ReferralResponse)
def update_referral(
    referral_id: int,
    update_data: ReferralUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update referral"""
    user_id = int(credentials.get("sub"))
    referral = ReferralService.update_referral(db, referral_id, user_id, update_data)
    return referral


@router.get("/referred-cases")
def get_referred_cases(
    skip: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get cases referred by this social worker"""
    user_id = int(credentials.get("sub"))
    return ReferralService.get_social_worker_referrals(db, user_id, skip, limit)


# ===== LAWYER ENDPOINTS (from referred perspective) =====

@router.get("/lawyer/{lawyer_id}/referrals", response_model=dict)
def get_lawyer_referrals(
    lawyer_id: int,
    skip: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get referrals sent to a specific lawyer"""
    user_id = int(credentials.get("sub"))
    # Verify user is social worker
    return ReferralService.get_lawyer_referrals(db, lawyer_id, skip, limit)


# ===== CLIENT ENDPOINTS (from referred perspective) =====

@router.get("/client/{citizen_id}/referrals", response_model=dict)
def get_client_referred_cases(
    citizen_id: int,
    skip: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get cases referred for a specific client"""
    user_id = int(credentials.get("sub"))
    return ReferralService.get_citizen_referred_cases(db, citizen_id, skip, limit)


# ===== DIRECTORY/SEARCH ENDPOINTS =====

@router.get("/lawyers/approved")
def get_approved_lawyers(
    specialization: Optional[str] = None,
    skip: int = Query(0),
    limit: int = Query(10),
    db: Session = Depends(get_db)
):
    """Get list of approved lawyers for referrals"""
    from app.database.models import Lawyer

    query = db.query(Lawyer).filter(Lawyer.verified == True)

    if specialization:
        query = query.filter(Lawyer.specialization.contains(specialization))

    total = query.count()
    lawyers = query.offset(skip).limit(limit).all()

    return {
        "total": total,
        "lawyers": [
            {
                "id": l.id,
                "name": l.name,
                "specialization": l.specialization,
                "experience": l.experience,
                "rating": float(l.rating) if l.rating else 0,
                "verified": l.verified,
            } for l in lawyers
        ],
        "skip": skip,
        "limit": limit
    }


# ===== DASHBOARD ENDPOINTS =====

@router.get("/dashboard", response_model=dict)
def get_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get social worker dashboard"""
    user_id = int(credentials.get("sub"))
    dashboard_data = SocialWorkerDashboardService.get_dashboard_data(db, user_id)
    return dashboard_data


@router.get("/dashboard/stats")
def get_dashboard_stats(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    user_id = int(credentials.get("sub"))
    stats = SocialWorkerDashboardService.get_dashboard_stats(db, user_id)
    return stats


@router.get("/dashboard/impact-report")
def get_impact_report(
    days: int = Query(30, ge=1, le=365),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get impact report for period"""
    user_id = int(credentials.get("sub"))
    report = SocialWorkerDashboardService.get_impact_report(db, user_id, days)
    return report


# ===== AGENCY ENDPOINTS =====

@router.get("/agency/{agency_id}/dashboard", response_model=dict)
def get_agency_dashboard(
    agency_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get agency dashboard"""
    user_id = int(credentials.get("sub"))
    dashboard_data = SocialWorkerDashboardService.get_agency_dashboard_data(db, agency_id)
    return dashboard_data


@router.get("/agency/{agency_id}/stats")
def get_agency_stats(
    agency_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get agency statistics"""
    user_id = int(credentials.get("sub"))
    stats = SocialWorkerDashboardService.get_agency_dashboard_stats(db, agency_id)
    return stats


@router.get("/agency/{agency_id}/workers", response_model=dict)
def get_agency_workers(
    agency_id: int,
    skip: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all workers in agency"""
    user_id = int(credentials.get("sub"))
    return SocialWorkerProfileService.get_agency_workers(db, agency_id, skip, limit)


# ===== COORDINATION MESSAGING (using existing DirectMessage) =====

@router.post("/messages/{recipient_id}")
def send_coordination_message(
    recipient_id: int,
    message_content: str,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Send coordination message to lawyer or client"""
    from app.database.models import DirectMessage
    from datetime import datetime, timezone

    user_id = int(credentials.get("sub"))

    db_message = DirectMessage(
        sender_id=user_id,
        receiver_id=recipient_id,
        message=message_content,
        is_read=False,
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)

    return {
        "id": db_message.id,
        "sender_id": db_message.sender_id,
        "receiver_id": db_message.receiver_id,
        "message": db_message.message,
        "created_at": db_message.created_at
    }


@router.get("/messages/{other_user_id}")
def get_coordination_messages(
    other_user_id: int,
    skip: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get coordination messages with lawyer or client"""
    from app.database.models import DirectMessage
    from sqlalchemy import or_

    user_id = int(credentials.get("sub"))

    messages = db.query(DirectMessage).filter(
        or_(
            (DirectMessage.sender_id == user_id) & (DirectMessage.receiver_id == other_user_id),
            (DirectMessage.sender_id == other_user_id) & (DirectMessage.receiver_id == user_id),
        )
    ).order_by(DirectMessage.created_at.desc()).offset(skip).limit(limit).all()

    return {
        "messages": [
            {
                "id": m.id,
                "sender_id": m.sender_id,
                "receiver_id": m.receiver_id,
                "message": m.message,
                "is_read": m.is_read,
                "created_at": m.created_at
            } for m in messages
        ],
        "skip": skip,
        "limit": limit
    }
