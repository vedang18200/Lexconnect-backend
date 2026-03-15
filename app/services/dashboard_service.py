"""Dashboard service for citizen dashboard data"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone
from app.database.models import (
    Case, Consultation, Payment, LawyerReview, Notification, User, Lawyer
)
from app.services.citizen_service import CitizenService
from app.services.payment_service import PaymentService
from app.api.schemas.citizen import DashboardStats


class DashboardService:
    """Service for citizen dashboard"""

    @staticmethod
    def get_dashboard_data(db: Session, citizen_id: int) -> dict:
        """Get complete dashboard data for a citizen"""

        # Get statistics
        stats = DashboardService.get_dashboard_stats(db, citizen_id)

        # Get recent cases
        cases = db.query(Case).filter(Case.user_id == citizen_id).order_by(
            Case.created_at.desc()
        ).limit(5).all()
        recent_cases = [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "category": c.category,
                "created_at": c.created_at,
                "lawyer_id": c.lawyer_id,
            } for c in cases
        ]

        # Get upcoming consultations
        now = datetime.now(timezone.utc)
        consultations = db.query(Consultation).filter(
            and_(
                Consultation.user_id == citizen_id,
                Consultation.consultation_date >= now,
                Consultation.status == "scheduled"
            )
        ).order_by(Consultation.consultation_date.asc()).limit(5).all()

        upcoming_consultations = [
            {
                "id": c.id,
                "consultation_date": c.consultation_date,
                "consultation_type": c.consultation_type,
                "status": c.status,
                "lawyer_id": c.lawyer_id,
                "fee_amount": float(c.fee_amount) if c.fee_amount else None,
            } for c in consultations
        ]

        # Get recent reviews written
        reviews = db.query(LawyerReview).filter(
            LawyerReview.citizen_id == citizen_id
        ).order_by(LawyerReview.created_at.desc()).limit(3).all()

        recent_reviews = [
            {
                "id": r.id,
                "lawyer_id": r.lawyer_id,
                "rating": r.rating,
                "title": r.title,
                "created_at": r.created_at,
            } for r in reviews
        ]

        # Get recent notifications
        notifications = db.query(Notification).filter(
            Notification.user_id == citizen_id
        ).order_by(Notification.created_at.desc()).limit(5).all()

        recent_notifications = [
            {
                "id": n.id,
                "notification_type": n.notification_type,
                "title": n.title,
                "message": n.message,
                "is_read": n.is_read,
                "created_at": n.created_at,
            } for n in notifications
        ]

        return {
            "stats": stats,
            "recent_cases": recent_cases,
            "upcoming_consultations": upcoming_consultations,
            "recent_reviews": recent_reviews,
            "recent_notifications": recent_notifications,
        }

    @staticmethod
    def get_dashboard_stats(db: Session, citizen_id: int) -> DashboardStats:
        """Get dashboard statistics"""

        # Case statistics
        total_cases = db.query(Case).filter(Case.user_id == citizen_id).count()
        active_cases = db.query(Case).filter(
            and_(Case.user_id == citizen_id, Case.status.in_(["open", "in_progress"]))
        ).count()
        resolved_cases = db.query(Case).filter(
            and_(Case.user_id == citizen_id, Case.status.in_(["closed", "resolved"]))
        ).count()

        # Consultation statistics
        total_consultations = db.query(Consultation).filter(
            Consultation.user_id == citizen_id
        ).count()

        now = datetime.now(timezone.utc)
        upcoming_consultations = db.query(Consultation).filter(
            and_(
                Consultation.user_id == citizen_id,
                Consultation.consultation_date >= now,
                Consultation.status == "scheduled"
            )
        ).count()

        # Payment statistics
        total_spent = db.query(func.sum(Payment.amount)).filter(
            and_(Payment.citizen_id == citizen_id, Payment.status == "completed")
        ).scalar()
        total_spent = float(total_spent) if total_spent else 0.0

        pending_payments = db.query(Payment).filter(
            and_(Payment.citizen_id == citizen_id, Payment.status.in_(["pending", "failed"]))
        ).count()

        # Notification statistics
        unread_notifications = db.query(Notification).filter(
            and_(Notification.user_id == citizen_id, Notification.is_read == False)
        ).count()

        return DashboardStats(
            total_cases=total_cases,
            active_cases=active_cases,
            resolved_cases=resolved_cases,
            total_consultations=total_consultations,
            upcoming_consultations=upcoming_consultations,
            total_spent=total_spent,
            pending_payments=pending_payments,
            unread_notifications=unread_notifications,
        )

    @staticmethod
    def get_cases_summary(db: Session, citizen_id: int):
        """Return top 4 active/recent cases for dashboard cards"""
        from app.api.schemas.citizen import CaseSummaryItem
        from sqlalchemy.orm import joinedload
        from datetime import date

        # Get top 4 most recent/active cases
        cases = (
            db.query(Case)
            .filter(Case.user_id == citizen_id)
            .order_by(Case.created_at.desc())
            .limit(4)
            .all()
        )

        result = []
        for case in cases:
            # Get lawyer name if assigned
            lawyer_name = None
            if case.lawyer_id:
                lawyer = db.query(Lawyer).filter(Lawyer.user_id == case.lawyer_id).first()
                if lawyer:
                    lawyer_name = lawyer.name
            # Get next hearing date from consultations (if any, future only)
            next_hearing = None
            consultation = (
                db.query(Consultation)
                .filter(
                    Consultation.case_id == case.id,
                    Consultation.consultation_date != None,
                    Consultation.consultation_date >= date.today()
                )
                .order_by(Consultation.consultation_date.asc())
                .first()
            )
            if consultation:
                next_hearing = consultation.consultation_date.date()

            result.append(CaseSummaryItem(
                id=case.id,
                title=case.title,
                lawyer=lawyer_name or "-",
                status=case.status,
                nextHearing=next_hearing,
                description=case.description or ""
            ))
        return result

    @staticmethod
    def get_consultation_summary(db: Session, citizen_id: int) -> dict:
        """Get detailed consultation summary"""
        consultations = db.query(Consultation).filter(
            Consultation.user_id == citizen_id
        ).all()

        status_breakdown = {}
        for consultation in consultations:
            status = consultation.status
            if status not in status_breakdown:
                status_breakdown[status] = 0
            status_breakdown[status] += 1

        type_breakdown = {}
        for consultation in consultations:
            consultation_type = consultation.consultation_type or "General"
            if consultation_type not in type_breakdown:
                type_breakdown[consultation_type] = 0
            type_breakdown[consultation_type] += 1

        total_fee = db.query(func.sum(Consultation.fee_amount)).filter(
            Consultation.user_id == citizen_id
        ).scalar()

        return {
            "total_consultations": len(consultations),
            "status_breakdown": status_breakdown,
            "type_breakdown": type_breakdown,
            "total_fee_spent": float(total_fee) if total_fee else 0.0,
        }

    @staticmethod
    def get_activity_summary(db: Session, citizen_id: int, days: int = 30) -> dict:
        """Get activity summary for last N days"""
        from datetime import timedelta

        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        cases_created = db.query(Case).filter(
            and_(Case.user_id == citizen_id, Case.created_at >= cutoff_date)
        ).count()

        consultations_booked = db.query(Consultation).filter(
            and_(Consultation.user_id == citizen_id, Consultation.created_at >= cutoff_date)
        ).count()

        payments_made = db.query(Payment).filter(
            and_(
                Payment.citizen_id == citizen_id,
                Payment.status == "completed",
                Payment.confirmed_at >= cutoff_date
            )
        ).count()

        reviews_written = db.query(LawyerReview).filter(
            and_(LawyerReview.citizen_id == citizen_id, LawyerReview.created_at >= cutoff_date)
        ).count()

        return {
            "period_days": days,
            "cases_created": cases_created,
            "consultations_booked": consultations_booked,
            "payments_made": payments_made,
            "reviews_written": reviews_written,
        }
