"""Citizen endpoints for profile, documents, reviews, payments, and dashboard"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.core.security import verify_token, get_current_user_id
from fastapi.security import HTTPAuthorizationCredentials
from app.database.models import User
from app.services.citizen_service import CitizenService
from app.services.document_service import DocumentService
from app.services.review_service import ReviewService
from app.services.payment_service import PaymentService
from app.services.dashboard_service import DashboardService
from app.services.two_factor_auth_service import TwoFactorAuthService
from app.api.schemas.citizen import (
    CitizenProfileResponse, CitizenProfileUpdate,
    DocumentUploadResponse, DocumentUploadCreate,
    LawyerReviewResponse, LawyerReviewCreate,
    PaymentResponse, PaymentCreate,
    NotificationResponse,
    TwoFactorAuthSetup, TwoFactorAuthVerify, TwoFactorAuthResponse,
    NotificationPreferencesResponse, NotificationPreferencesUpdate,
    BillingHistoryResponse
)
from typing import List
from datetime import date
import json
import os

def require_citizen_user(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db),
):
    """Allow access only to citizen users for this router."""
    user_id = int(credentials.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.user_type != "citizen":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only citizen users can access this endpoint",
        )
    return user_id


router = APIRouter(
    prefix="/citizens",
    tags=["Citizens"],
    dependencies=[Depends(require_citizen_user)],
)


# === PROFILE ENDPOINTS ===

@router.get("/profile", response_model=CitizenProfileResponse)
def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get citizen profile"""
    user_id = int(credentials.get("sub"))  # Extract from token
    # Auto-create profile on first access so dashboard/profile pages don't fail with 404.
    profile = CitizenService.get_or_create_citizen_profile(db, user_id)
    user = db.query(User).filter(User.id == user_id).first()
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "email": user.email if user else None,
        "phone": user.phone if user else None,
        "date_of_birth": profile.date_of_birth,
        "gender": profile.gender,
        "occupation": profile.occupation,
        "aadhar_number_masked": CitizenService.mask_aadhar_number(profile.aadhar_number),
        "address": profile.address,
        "city": profile.city,
        "state": profile.state,
        "pincode": profile.pincode,
        "bio": profile.bio,
        "profile_picture_url": profile.profile_picture_url,
        "is_kyc_verified": profile.is_kyc_verified,
        "kyc_verified_at": profile.kyc_verified_at,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


@router.post("/profile", response_model=CitizenProfileResponse)
def create_or_update_profile(
    profile_update: CitizenProfileUpdate | None = None,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create or update citizen profile"""
    user_id = int(credentials.get("sub"))
    profile_update = profile_update or CitizenProfileUpdate()
    profile = CitizenService.update_citizen_profile(db, user_id, profile_update)
    user = db.query(User).filter(User.id == user_id).first()
    return {
        "id": profile.id,
        "user_id": profile.user_id,
        "full_name": profile.full_name,
        "email": user.email if user else None,
        "phone": user.phone if user else None,
        "date_of_birth": profile.date_of_birth,
        "gender": profile.gender,
        "occupation": profile.occupation,
        "aadhar_number_masked": CitizenService.mask_aadhar_number(profile.aadhar_number),
        "address": profile.address,
        "city": profile.city,
        "state": profile.state,
        "pincode": profile.pincode,
        "bio": profile.bio,
        "profile_picture_url": profile.profile_picture_url,
        "is_kyc_verified": profile.is_kyc_verified,
        "kyc_verified_at": profile.kyc_verified_at,
        "created_at": profile.created_at,
        "updated_at": profile.updated_at,
    }


# === 2FA ENDPOINTS ===

@router.post("/2fa/setup", response_model=dict)
def setup_2fa(
    setup: TwoFactorAuthSetup,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Setup two-factor authentication"""
    user_id = int(credentials.get("sub"))
    two_fa = TwoFactorAuthService.setup_2fa(
        db, user_id, setup.auth_method, setup.phone_number
    )

    response = {
        "id": two_fa.id,
        "auth_method": two_fa.auth_method,
        "is_enabled": two_fa.is_enabled,
        "backup_codes": None
    }

    # If TOTP, return backup codes and QR code URL
    if setup.auth_method.upper() == "TOTP":
        qr_url = TwoFactorAuthService.get_totp_qr_code(db, user_id)
        response["qr_code_url"] = qr_url
        response["backup_codes"] = json.loads(two_fa.backup_codes) if two_fa.backup_codes else []

    return response


@router.post("/2fa/verify")
def verify_2fa_code(
    verify: TwoFactorAuthVerify,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Verify 2FA code"""
    user_id = int(credentials.get("sub"))
    is_valid = TwoFactorAuthService.verify_2fa_code(db, user_id, verify.code)
    return {"is_valid": is_valid, "message": "Code verified successfully"}


@router.post("/2fa/enable", response_model=TwoFactorAuthResponse)
def enable_2fa(
    verify: TwoFactorAuthVerify = None,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Enable two-factor authentication"""
    user_id = int(credentials.get("sub"))
    code = verify.code if verify else None
    two_fa = TwoFactorAuthService.enable_2fa(db, user_id, code)
    return two_fa


@router.post("/2fa/disable", response_model=TwoFactorAuthResponse)
def disable_2fa(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Disable two-factor authentication"""
    user_id = int(credentials.get("sub"))
    two_fa = TwoFactorAuthService.disable_2fa(db, user_id)
    return two_fa


@router.get("/2fa/status", response_model=TwoFactorAuthResponse)
def get_2fa_status(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get 2FA status"""
    user_id = int(credentials.get("sub"))
    two_fa = TwoFactorAuthService.get_2fa_status(db, user_id)
    return two_fa


@router.post("/2fa/backup-codes")
def regenerate_backup_codes(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Regenerate backup codes"""
    user_id = int(credentials.get("sub"))
    return TwoFactorAuthService.regenerate_backup_codes(db, user_id)


@router.get("/2fa/qr-code")
def get_qr_code(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get QR code for TOTP"""
    user_id = int(credentials.get("sub"))
    qr_url = TwoFactorAuthService.get_totp_qr_code(db, user_id)
    return {"qr_code_url": qr_url}


# === DOCUMENT ENDPOINTS ===

@router.post("/documents", response_model=DocumentUploadResponse)
async def upload_document(
    case_id: int = Query(None),
    document_type: str = Query(None),
    description: str = Query(None),
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Upload a document for a case"""
    user_id = int(credentials.get("sub"))

    # Simulate file storage (in production, use S3, GCS, etc.)
    file_url = f"/files/{file.filename}"
    file_size = len(await file.read())
    mime_type = file.content_type

    document = DocumentUploadCreate(
        case_id=case_id,
        document_type=document_type,
        file_name=file.filename,
        description=description
    )

    db_document = DocumentService.upload_document(
        db, user_id, document, file_url, file_size, mime_type, user_id
    )
    return db_document


@router.get("/documents", response_model=dict)
def list_documents(
    case_id: int = Query(None),
    skip: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List documents"""
    user_id = int(credentials.get("sub"))

    if case_id:
        return DocumentService.get_documents_by_case(db, case_id, user_id, skip, limit)
    else:
        return DocumentService.get_documents_by_user(db, user_id, skip, limit)


@router.get("/documents/{document_id}", response_model=DocumentUploadResponse)
def get_document(
    document_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get a specific document"""
    user_id = int(credentials.get("sub"))
    document = DocumentService.get_document(db, document_id, user_id)
    return document


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    user_id = int(credentials.get("sub"))
    DocumentService.delete_document(db, document_id, user_id)
    return {"message": "Document deleted successfully"}


# === REVIEW ENDPOINTS ===

@router.post("/reviews", response_model=LawyerReviewResponse)
def create_review(
    review: LawyerReviewCreate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create a review for a lawyer"""
    user_id = int(credentials.get("sub"))
    db_review = ReviewService.create_review(db, user_id, review)
    return db_review


@router.get("/reviews/my-reviews", response_model=dict)
def get_my_reviews(
    skip: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get reviews written by the citizen"""
    user_id = int(credentials.get("sub"))
    return ReviewService.get_citizen_reviews(db, user_id, skip, limit)


@router.get("/reviews/{review_id}", response_model=LawyerReviewResponse)
def get_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific review"""
    review = ReviewService.get_review(db, review_id)
    return review


@router.put("/reviews/{review_id}", response_model=LawyerReviewResponse)
def update_review(
    review_id: int,
    review_update: dict,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update a review"""
    user_id = int(credentials.get("sub"))
    updated_review = ReviewService.update_review(db, review_id, user_id, review_update)
    return updated_review


@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete a review"""
    user_id = int(credentials.get("sub"))
    ReviewService.delete_review(db, review_id, user_id)
    return {"message": "Review deleted successfully"}


@router.post("/reviews/{review_id}/helpful")
def mark_helpful(
    review_id: int,
    db: Session = Depends(get_db)
):
    """Mark review as helpful"""
    review = ReviewService.mark_helpful(db, review_id)
    return {"message": "Marked as helpful", "helpful_count": review.helpful_count}


@router.post("/reviews/{review_id}/unhelpful")
def mark_unhelpful(
    review_id: int,
    db: Session = Depends(get_db)
):
    """Mark review as unhelpful"""
    review = ReviewService.mark_unhelpful(db, review_id)
    return {"message": "Marked as unhelpful", "unhelpful_count": review.unhelpful_count}


# === PAYMENT ENDPOINTS ===

@router.post("/payments", response_model=PaymentResponse)
def create_payment(
    payment: PaymentCreate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create a payment"""
    user_id = int(credentials.get("sub"))
    db_payment = PaymentService.create_payment(
        db,
        user_id,
        payment.lawyer_id,
        payment.amount,
        payment.payment_method,
        payment.consultation_id,
        payment.case_id,
        payment.description
    )
    return db_payment


@router.get("/payments", response_model=dict)
def list_payments(
    skip: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List citizen's payments"""
    user_id = int(credentials.get("sub"))
    return PaymentService.get_citizen_payments(db, user_id, skip, limit)


@router.get("/billing-history", response_model=BillingHistoryResponse)
def get_billing_history(
    skip: int = Query(0),
    limit: int = Query(10),
    status: str | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get billing history for profile tab."""
    user_id = int(credentials.get("sub"))
    return PaymentService.get_billing_history(
        db,
        user_id,
        skip=skip,
        limit=limit,
        status_filter=status,
        from_date=from_date,
        to_date=to_date,
    )


@router.get("/notification-preferences", response_model=NotificationPreferencesResponse)
def get_notification_preferences(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get notification preferences for current citizen."""
    user_id = int(credentials.get("sub"))
    return CitizenService.get_or_create_notification_preferences(db, user_id)


@router.put("/notification-preferences", response_model=NotificationPreferencesResponse)
def update_notification_preferences(
    payload: NotificationPreferencesUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update notification preferences for current citizen."""
    user_id = int(credentials.get("sub"))
    return CitizenService.update_notification_preferences(db, user_id, payload.model_dump())


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get a specific payment"""
    user_id = int(credentials.get("sub"))
    payment = PaymentService.get_payment(db, payment_id, user_id)
    return payment


@router.post("/payments/{payment_id}/confirm", response_model=PaymentResponse)
def confirm_payment(
    payment_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Confirm payment completion"""
    user_id = int(credentials.get("sub"))
    payment = PaymentService.confirm_payment(db, payment_id, user_id)
    return payment


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
def refund_payment(
    payment_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Request refund for a payment"""
    user_id = int(credentials.get("sub"))
    payment = PaymentService.refund_payment(db, payment_id, user_id)
    return payment


# === DASHBOARD ENDPOINTS ===

@router.get("/dashboard", response_model=dict)
def get_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get citizen dashboard with all statistics and recent activity"""
    user_id = int(credentials.get("sub"))
    dashboard_data = DashboardService.get_dashboard_data(db, user_id)
    return dashboard_data


@router.get("/dashboard/stats")
def get_dashboard_stats(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    user_id = int(credentials.get("sub"))
    stats = DashboardService.get_dashboard_stats(db, user_id)
    return stats.model_dump()



from app.api.schemas.citizen import CaseSummaryItem

@router.get("/dashboard/cases-summary", response_model=List[CaseSummaryItem])
def get_cases_summary(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get top 4 case summary items for dashboard cards"""
    user_id = int(credentials.get("sub"))
    return DashboardService.get_cases_summary(db, user_id)


@router.get("/dashboard/consultations-summary")
def get_consultations_summary(
    status: str | None = Query(default=None, description="Filter by status (scheduled/completed/cancelled/all)"),
    mode: str | None = Query(default=None, description="Filter by consultation mode/type (video/phone/chat/all)"),
    q: str | None = Query(default=None, description="Search by lawyer name, consultation ID, or case title"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=0, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get detailed consultation summary"""
    user_id = int(credentials.get("sub"))
    # Some frontends send limit=0 initially; treat that as default page size.
    effective_limit = 20 if limit == 0 else limit
    return DashboardService.get_consultation_summary(
        db,
        user_id,
        status_filter=status,
        mode_filter=mode,
        query=q,
        skip=skip,
        limit=effective_limit,
    )


@router.get("/dashboard/consultations/{consultation_id}/details")
def get_consultation_details(
    consultation_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get consultation details for the View Details modal."""
    user_id = int(credentials.get("sub"))
    return DashboardService.get_consultation_detail(db, user_id, consultation_id)


@router.get("/dashboard/activity")
def get_activity_summary(
    days: int = Query(30, ge=1, le=365),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get activity summary for specified period"""
    user_id = int(credentials.get("sub"))
    return DashboardService.get_activity_summary(db, user_id, days)
