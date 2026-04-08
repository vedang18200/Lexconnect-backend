"""Citizen service for managing citizen profiles and related operations"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timezone
from fastapi import HTTPException, status
from app.database.models import (
    User, CitizenProfile, Case, Consultation, DirectMessage,
    DocumentUpload, LawyerReview, Payment, Lawyer, NotificationPreference
)
from app.api.schemas.citizen import (
    CitizenProfileCreate, CitizenProfileUpdate, CitizenProfileResponse
)
from app.core.security import get_password_hash


class CitizenService:
    """Service for citizen profile management"""

    @staticmethod
    def get_or_create_citizen_profile(db: Session, user_id: int) -> CitizenProfile:
        """Get or create a citizen profile"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        if user.user_type != "citizen":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only citizens can have a citizen profile"
            )
        profile = db.query(CitizenProfile).filter(CitizenProfile.user_id == user_id).first()
        if not profile:
            profile = CitizenProfile(
                user_id=user_id,
                full_name=user.username,
                city=user.location,
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            return profile

        # Backfill profile defaults for users who already had an empty profile row.
        is_updated = False
        if not profile.full_name and user.username:
            profile.full_name = user.username
            is_updated = True
        if not profile.city and user.location:
            profile.city = user.location
            is_updated = True

        if is_updated:
            profile.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(profile)
        return profile

    @staticmethod
    def update_citizen_profile(
        db: Session, user_id: int, profile_update: CitizenProfileUpdate
    ) -> CitizenProfile:
        """Update citizen profile"""
        profile = CitizenService.get_or_create_citizen_profile(db, user_id)
        user = db.query(User).filter(User.id == user_id).first()

        update_data = profile_update.model_dump(exclude_unset=True)

        # Update user-scoped fields from profile page
        email = update_data.pop("email", None)
        phone = update_data.pop("phone", None)

        if email and user:
            existing_user = db.query(User).filter(User.email == email, User.id != user_id).first()
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
            user.email = email

        if phone is not None and user:
            user.phone = phone

        # Persist all profile fields, including secure KYC fields.
        for field, value in update_data.items():
            if value is not None and hasattr(profile, field):
                setattr(profile, field, value)

        profile.updated_at = datetime.now(timezone.utc)
        if user:
            user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def mask_aadhar_number(aadhar_number: str | None) -> str | None:
        """Return a masked Aadhaar number for safe API responses."""
        if not aadhar_number:
            return None
        visible = aadhar_number[-4:]
        return f"XXXX-XXXX-{visible}"

    @staticmethod
    def get_or_create_notification_preferences(db: Session, user_id: int) -> NotificationPreference:
        """Get or create default notification preferences for a user."""
        prefs = db.query(NotificationPreference).filter(NotificationPreference.user_id == user_id).first()
        if prefs:
            return prefs

        prefs = NotificationPreference(user_id=user_id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
        return prefs

    @staticmethod
    def update_notification_preferences(db: Session, user_id: int, updates: dict) -> NotificationPreference:
        """Update notification preferences for a user."""
        prefs = CitizenService.get_or_create_notification_preferences(db, user_id)

        for field, value in updates.items():
            if hasattr(prefs, field):
                setattr(prefs, field, value)

        prefs.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(prefs)
        return prefs

    @staticmethod
    def get_citizen_profile(db: Session, user_id: int) -> CitizenProfile:
        """Get citizen profile"""
        user = db.query(User).filter(User.id == user_id).first()
        if user and user.user_type != "citizen":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only citizens can access a citizen profile"
            )
        profile = db.query(CitizenProfile).filter(CitizenProfile.user_id == user_id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Citizen profile not found"
            )
        return profile

    @staticmethod
    def get_cases_by_citizen(db: Session, user_id: int, skip: int = 0, limit: int = 10):
        """Get all cases for a citizen"""
        total = db.query(Case).filter(Case.user_id == user_id).count()
        cases = db.query(Case).filter(Case.user_id == user_id).offset(skip).limit(limit).all()
        return {"total": total, "cases": cases}

    @staticmethod
    def get_consultations_by_citizen(db: Session, user_id: int, skip: int = 0, limit: int = 10):
        """Get all consultations for a citizen"""
        total = db.query(Consultation).filter(Consultation.user_id == user_id).count()
        consultations = (
            db.query(Consultation)
            .filter(Consultation.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {"total": total, "consultations": consultations}

    @staticmethod
    def get_active_cases(db: Session, user_id: int) -> int:
        """Get count of active cases"""
        return db.query(Case).filter(
            and_(Case.user_id == user_id, Case.status.in_(["open", "in_progress"]))
        ).count()

    @staticmethod
    def get_resolved_cases(db: Session, user_id: int) -> int:
        """Get count of resolved cases"""
        return db.query(Case).filter(
            and_(Case.user_id == user_id, Case.status.in_(["closed", "resolved"]))
        ).count()

    @staticmethod
    def get_upcoming_consultations(db: Session, user_id: int):
        """Get upcoming consultations"""
        now = datetime.now(timezone.utc)
        return db.query(Consultation).filter(
            and_(
                Consultation.user_id == user_id,
                Consultation.consultation_date >= now,
                Consultation.status == "scheduled"
            )
        ).all()

    @staticmethod
    def get_total_spent(db: Session, user_id: int) -> float:
        """Get total amount spent by citizen on consultations"""
        total = db.query(func.sum(Payment.amount)).filter(
            and_(Payment.citizen_id == user_id, Payment.status == "completed")
        ).scalar()
        return float(total) if total else 0.0

    @staticmethod
    def get_pending_payments(db: Session, user_id: int) -> int:
        """Get count of pending payments"""
        return db.query(Payment).filter(
            and_(Payment.citizen_id == user_id, Payment.status.in_(["pending", "failed"]))
        ).count()

    @staticmethod
    def update_user_info(db: Session, user_id: int, **kwargs) -> User:
        """Update user basic info"""
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        for field, value in kwargs.items():
            if value is not None and hasattr(user, field) and field != "password":
                setattr(user, field, value)

        if "password" in kwargs and kwargs["password"]:
            user.password = get_password_hash(kwargs["password"])

        user.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def verify_kyc(db: Session, user_id: int) -> CitizenProfile:
        """Mark citizen as KYC verified (admin only)"""
        profile = CitizenService.get_citizen_profile(db, user_id)
        profile.is_kyc_verified = True
        profile.kyc_verified_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(profile)
        return profile
