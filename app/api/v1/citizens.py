"""Citizen endpoints for profile, documents, reviews, payments, and dashboard"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.core.security import verify_token, get_current_user_id
from fastapi.security import HTTPAuthorizationCredentials
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
    TwoFactorAuthSetup, TwoFactorAuthVerify, TwoFactorAuthResponse
)
from typing import List
import os

router = APIRouter(prefix="/citizens", tags=["Citizens"])


# === PROFILE ENDPOINTS ===

@router.get("/profile", response_model=CitizenProfileResponse)
def get_profile(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get citizen profile"""
    user_id = int(credentials.get("sub"))  # Extract from token
    profile = CitizenService.get_citizen_profile(db, user_id)
    return profile


@router.post("/profile", response_model=CitizenProfileResponse)
def create_or_update_profile(
    profile_update: CitizenProfileUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create or update citizen profile"""
    user_id = int(credentials.get("sub"))
    profile = CitizenService.update_citizen_profile(db, user_id, profile_update)
    return profile


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
        response["backup_codes"] = two_fa.backup_codes

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
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get detailed consultation summary"""
    user_id = int(credentials.get("sub"))
    return DashboardService.get_consultation_summary(db, user_id)


@router.get("/dashboard/activity")
def get_activity_summary(
    days: int = Query(30, ge=1, le=365),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get activity summary for specified period"""
    user_id = int(credentials.get("sub"))
    return DashboardService.get_activity_summary(db, user_id, days)
