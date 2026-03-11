"""Social worker services"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, status
from app.database.models import (
    SocialWorkerProfile, Referral, Agency, User, Case, Consultation
)
from app.api.schemas.social_worker import (
    SocialWorkerProfileCreate, ReferralCreate, ReferralUpdate
)


class SocialWorkerProfileService:
    """Service for social worker profile management"""

    @staticmethod
    def get_or_create_profile(
        db: Session, user_id: int, profile: SocialWorkerProfileCreate
    ) -> SocialWorkerProfile:
        """Get or create social worker profile"""
        existing = db.query(SocialWorkerProfile).filter(
            SocialWorkerProfile.user_id == user_id
        ).first()

        if existing:
            return existing

        # Verify agency exists
        agency = db.query(Agency).filter(Agency.id == profile.agency_id).first()
        if not agency:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agency not found"
            )

        db_profile = SocialWorkerProfile(
            user_id=user_id,
            agency_id=profile.agency_id,
            license_number=profile.license_number,
            specialization=profile.specialization,
            bio=profile.bio
        )
        db.add(db_profile)
        db.commit()
        db.refresh(db_profile)
        return db_profile

    @staticmethod
    def get_profile(db: Session, user_id: int) -> SocialWorkerProfile:
        """Get social worker profile"""
        profile = db.query(SocialWorkerProfile).filter(
            SocialWorkerProfile.user_id == user_id
        ).first()

        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Social worker profile not found"
            )
        return profile

    @staticmethod
    def update_profile(
        db: Session, user_id: int, update_data: dict
    ) -> SocialWorkerProfile:
        """Update social worker profile"""
        profile = SocialWorkerProfileService.get_profile(db, user_id)

        for key, value in update_data.items():
            if value is not None and hasattr(profile, key):
                setattr(profile, key, value)

        profile.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_agency_workers(
        db: Session, agency_id: int, skip: int = 0, limit: int = 10
    ) -> dict:
        """Get all workers in an agency"""
        total = db.query(SocialWorkerProfile).filter(
            SocialWorkerProfile.agency_id == agency_id
        ).count()

        workers = db.query(SocialWorkerProfile).filter(
            SocialWorkerProfile.agency_id == agency_id
        ).offset(skip).limit(limit).all()

        return {
            "total": total,
            "workers": workers,
            "skip": skip,
            "limit": limit
        }


class ReferralService:
    """Service for referral management"""

    @staticmethod
    def create_referral(
        db: Session, social_worker_id: int, referral: ReferralCreate
    ) -> Referral:
        """Create a referral from social worker to lawyer"""
        # Verify lawyer exists and is verified
        lawyer = db.query(User).filter(User.id == referral.lawyer_id).first()
        if not lawyer or lawyer.user_type != "lawyer":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer not found"
            )

        # Verify citizen exists
        citizen = db.query(User).filter(User.id == referral.citizen_id).first()
        if not citizen or citizen.user_type != "citizen":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Citizen not found"
            )

        db_referral = Referral(
            social_worker_id=social_worker_id,
            lawyer_id=referral.lawyer_id,
            citizen_id=referral.citizen_id,
            referral_reason=referral.referral_reason,
            case_category=referral.case_category,
            status="pending"
        )
        db.add(db_referral)
        db.commit()
        db.refresh(db_referral)

        # Update social worker stats
        profile = db.query(SocialWorkerProfile).filter(
            SocialWorkerProfile.user_id == social_worker_id
        ).first()
        if profile:
            profile.total_referrals += 1
            db.commit()

        return db_referral

    @staticmethod
    def get_referral(db: Session, referral_id: int, user_id: int) -> Referral:
        """Get referral details"""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()

        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referral not found"
            )

        # Check access - social worker (creator) or lawyer/citizen in referral
        user = db.query(User).filter(User.id == user_id).first()
        if (user_id != referral.social_worker_id and
            user_id != referral.lawyer_id and
            user_id != referral.citizen_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this referral"
            )

        return referral

    @staticmethod
    def get_social_worker_referrals(
        db: Session, social_worker_id: int, skip: int = 0, limit: int = 10
    ) -> dict:
        """Get referrals created by social worker"""
        total = db.query(Referral).filter(
            Referral.social_worker_id == social_worker_id
        ).count()

        referrals = db.query(Referral).filter(
            Referral.social_worker_id == social_worker_id
        ).order_by(Referral.created_at.desc()).offset(skip).limit(limit).all()

        return {
            "total": total,
            "referrals": referrals,
            "skip": skip,
            "limit": limit
        }

    @staticmethod
    def get_referrals_by_status(
        db: Session, social_worker_id: int, status: str, skip: int = 0, limit: int = 10
    ) -> dict:
        """Get referrals by status"""
        total = db.query(Referral).filter(
            and_(
                Referral.social_worker_id == social_worker_id,
                Referral.status == status
            )
        ).count()

        referrals = db.query(Referral).filter(
            and_(
                Referral.social_worker_id == social_worker_id,
                Referral.status == status
            )
        ).order_by(Referral.created_at.desc()).offset(skip).limit(limit).all()

        return {
            "total": total,
            "referrals": referrals,
            "skip": skip,
            "limit": limit
        }

    @staticmethod
    def update_referral(
        db: Session, referral_id: int, user_id: int, update_data: ReferralUpdate
    ) -> Referral:
        """Update referral"""
        referral = db.query(Referral).filter(Referral.id == referral_id).first()

        if not referral:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Referral not found"
            )

        # Only social worker can update
        if user_id != referral.social_worker_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this referral"
            )

        if update_data.status:
            referral.status = update_data.status
            if update_data.status == "accepted":
                referral.accepted_date = datetime.now(timezone.utc)
            elif update_data.status == "completed":
                referral.completed_date = datetime.now(timezone.utc)

        if update_data.outcome:
            referral.outcome = update_data.outcome
            if update_data.outcome == "resolved" or update_data.outcome == "successful":
                profile = db.query(SocialWorkerProfile).filter(
                    SocialWorkerProfile.user_id == user_id
                ).first()
                if profile:
                    profile.successful_referrals += 1

        if update_data.outcome_notes:
            referral.outcome_notes = update_data.outcome_notes

        referral.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(referral)
        return referral

    @staticmethod
    def get_lawyer_referrals(
        db: Session, lawyer_id: int, skip: int = 0, limit: int = 10
    ) -> dict:
        """Get referrals received by lawyer"""
        total = db.query(Referral).filter(
            Referral.lawyer_id == lawyer_id
        ).count()

        referrals = db.query(Referral).filter(
            Referral.lawyer_id == lawyer_id
        ).order_by(Referral.created_at.desc()).offset(skip).limit(limit).all()

        return {
            "total": total,
            "referrals": referrals,
            "skip": skip,
            "limit": limit
        }

    @staticmethod
    def get_citizen_referred_cases(
        db: Session, citizen_id: int, skip: int = 0, limit: int = 10
    ) -> dict:
        """Get cases referred for citizen"""
        total = db.query(Referral).filter(
            Referral.citizen_id == citizen_id
        ).count()

        referrals = db.query(Referral).filter(
            Referral.citizen_id == citizen_id
        ).order_by(Referral.created_at.desc()).offset(skip).limit(limit).all()

        return {
            "total": total,
            "referrals": referrals,
            "skip": skip,
            "limit": limit
        }


class SocialWorkerDashboardService:
    """Service for social worker dashboards and reporting"""

    @staticmethod
    def get_dashboard_stats(db: Session, social_worker_id: int) -> dict:
        """Get social worker dashboard statistics"""
        total_referrals = db.query(Referral).filter(
            Referral.social_worker_id == social_worker_id
        ).count()

        pending_referrals = db.query(Referral).filter(
            and_(
                Referral.social_worker_id == social_worker_id,
                Referral.status == "pending"
            )
        ).count()

        accepted_referrals = db.query(Referral).filter(
            and_(
                Referral.social_worker_id == social_worker_id,
                Referral.status.in_(["accepted", "in_progress"])
            )
        ).count()

        completed_referrals = db.query(Referral).filter(
            and_(
                Referral.social_worker_id == social_worker_id,
                Referral.status.in_(["completed", "closed"])
            )
        ).count()

        successful_referrals = db.query(Referral).filter(
            and_(
                Referral.social_worker_id == social_worker_id,
                Referral.outcome == "resolved"
            )
        ).count()

        success_rate = (
            (successful_referrals / total_referrals * 100) if total_referrals > 0 else 0
        )

        # Calculate average days to completion
        completed = db.query(Referral).filter(
            and_(
                Referral.social_worker_id == social_worker_id,
                Referral.completed_date.isnot(None)
            )
        ).all()

        avg_days = 0
        if completed:
            total_days = sum(
                (r.completed_date - r.referral_date).days for r in completed
            )
            avg_days = total_days / len(completed)

        return {
            "total_referrals": total_referrals,
            "pending_referrals": pending_referrals,
            "accepted_referrals": accepted_referrals,
            "completed_referrals": completed_referrals,
            "successful_referrals": successful_referrals,
            "success_rate": success_rate,
            "avg_days_to_completion": avg_days,
        }

    @staticmethod
    def get_dashboard_data(db: Session, social_worker_id: int) -> dict:
        """Get complete social worker dashboard data"""
        stats = SocialWorkerDashboardService.get_dashboard_stats(db, social_worker_id)

        # Recent referrals
        recent_referrals = db.query(Referral).filter(
            Referral.social_worker_id == social_worker_id
        ).order_by(Referral.created_at.desc()).limit(5).all()

        recent_referrals_data = [
            {
                "id": r.id,
                "lawyer_id": r.lawyer_id,
                "citizen_id": r.citizen_id,
                "status": r.status,
                "referral_date": r.referral_date,
            } for r in recent_referrals
        ]

        # Pending referrals
        pending = db.query(Referral).filter(
            and_(
                Referral.social_worker_id == social_worker_id,
                Referral.status == "pending"
            )
        ).order_by(Referral.created_at.asc()).limit(5).all()

        pending_data = [
            {
                "id": r.id,
                "lawyer_id": r.lawyer_id,
                "citizen_id": r.citizen_id,
                "case_category": r.case_category,
                "referral_date": r.referral_date,
            } for r in pending
        ]

        return {
            "stats": stats,
            "recent_referrals": recent_referrals_data,
            "pending_referrals": pending_data,
        }

    @staticmethod
    def get_impact_report(db: Session, social_worker_id: int, days: int = 30) -> dict:
        """Get impact report for period"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        referrals_in_period = db.query(Referral).filter(
            and_(
                Referral.social_worker_id == social_worker_id,
                Referral.referral_date >= cutoff_date
            )
        ).all()

        resolved_in_period = [
            r for r in referrals_in_period
            if r.outcome == "resolved" and r.completed_date
        ]

        ongoing_in_period = [
            r for r in referrals_in_period
            if r.outcome in ["resolved", "ongoing"] or r.outcome is None
        ]

        return {
            "period_days": days,
            "total_referrals": len(referrals_in_period),
            "resolved_cases": len(resolved_in_period),
            "ongoing_cases": len(ongoing_in_period),
            "resolution_rate": (
                len(resolved_in_period) / len(referrals_in_period) * 100
                if referrals_in_period else 0
            ),
            "case_categories": self._get_category_breakdown(referrals_in_period),
        }

    @staticmethod
    def _get_category_breakdown(referrals: list) -> dict:
        """Get case category breakdown"""
        breakdown = {}
        for r in referrals:
            category = r.case_category or "Uncategorized"
            if category not in breakdown:
                breakdown[category] = 0
            breakdown[category] += 1
        return breakdown

    @staticmethod
    def get_agency_dashboard_stats(db: Session, agency_id: int) -> dict:
        """Get agency-level dashboard statistics"""
        # Get all social workers in agency
        workers = db.query(SocialWorkerProfile).filter(
            SocialWorkerProfile.agency_id == agency_id
        ).all()

        worker_ids = [w.user_id for w in workers]

        # Calculate stats
        total_social_workers = len(workers)

        total_referrals = db.query(Referral).filter(
            Referral.social_worker_id.in_(worker_ids)
        ).count()

        successful_referrals = db.query(Referral).filter(
            and_(
                Referral.social_worker_id.in_(worker_ids),
                Referral.outcome == "resolved"
            )
        ).count()

        pending_referrals = db.query(Referral).filter(
            and_(
                Referral.social_worker_id.in_(worker_ids),
                Referral.status == "pending"
            )
        ).count()

        success_rate = (
            (successful_referrals / total_referrals * 100) if total_referrals > 0 else 0
        )

        return {
            "total_social_workers": total_social_workers,
            "total_referrals": total_referrals,
            "successful_referrals": successful_referrals,
            "pending_referrals": pending_referrals,
            "success_rate": success_rate,
        }

    @staticmethod
    def get_agency_dashboard_data(db: Session, agency_id: int) -> dict:
        """Get complete agency dashboard data"""
        stats = SocialWorkerDashboardService.get_agency_dashboard_stats(db, agency_id)

        # Get workers and their performance
        workers = db.query(SocialWorkerProfile).filter(
            SocialWorkerProfile.agency_id == agency_id
        ).all()

        worker_ids = [w.user_id for w in workers]

        top_workers = []
        for worker in workers:
            referral_count = db.query(Referral).filter(
                Referral.social_worker_id == worker.user_id
            ).count()
            successful = db.query(Referral).filter(
                and_(
                    Referral.social_worker_id == worker.user_id,
                    Referral.outcome == "resolved"
                )
            ).count()

            top_workers.append({
                "worker_id": worker.user_id,
                "total_referrals": referral_count,
                "successful_referrals": successful,
                "success_rate": (
                    (successful / referral_count * 100) if referral_count > 0 else 0
                ),
            })

        top_workers.sort(key=lambda x: x["success_rate"], reverse=True)

        # Recent referrals
        recent_referrals = db.query(Referral).filter(
            Referral.social_worker_id.in_(worker_ids)
        ).order_by(Referral.created_at.desc()).limit(10).all()

        # Category breakdown
        all_referrals = db.query(Referral).filter(
            Referral.social_worker_id.in_(worker_ids)
        ).all()

        category_breakdown = {}
        for r in all_referrals:
            category = r.case_category or "Uncategorized"
            if category not in category_breakdown:
                category_breakdown[category] = 0
            category_breakdown[category] += 1

        # Lawyer collaboration stats
        lawyer_collaborations = {}
        for r in all_referrals:
            lawyer_id = r.lawyer_id
            if lawyer_id not in lawyer_collaborations:
                lawyer_collaborations[lawyer_id] = {"referrals": 0, "successful": 0}
            lawyer_collaborations[lawyer_id]["referrals"] += 1
            if r.outcome == "resolved":
                lawyer_collaborations[lawyer_id]["successful"] += 1

        return {
            "stats": stats,
            "top_performing_workers": top_workers[:5],
            "recent_referrals": recent_referrals,
            "case_category_breakdown": category_breakdown,
            "lawyer_collaboration_stats": lawyer_collaborations,
        }
