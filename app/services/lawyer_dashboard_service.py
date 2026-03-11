"""Lawyer dashboard and analytics service"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from app.database.models import (
    Case, Consultation, Payment, LawyerReview, User, Invoice, CaseNote, Lawyer
)


class LawyerDashboardService:
    """Service for lawyer dashboard analytics"""

    @staticmethod
    def get_dashboard_data(db: Session, lawyer_id: int) -> dict:
        """Get complete dashboard data for a lawyer"""

        # Get statistics
        stats = LawyerDashboardService.get_dashboard_stats(db, lawyer_id)

        # Get recent cases
        cases = db.query(Case).filter(Case.lawyer_id == lawyer_id).order_by(
            Case.updated_at.desc()
        ).limit(5).all()
        recent_cases = [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
                "category": c.category,
                "client_id": c.user_id,
                "created_at": c.created_at,
            } for c in cases
        ]

        # Get upcoming consultations
        now = datetime.now(timezone.utc)
        consultations = db.query(Consultation).filter(
            and_(
                Consultation.lawyer_id == lawyer_id,
                Consultation.consultation_date >= now,
                Consultation.status == "scheduled"
            )
        ).order_by(Consultation.consultation_date.asc()).limit(5).all()

        upcoming_consultations = [
            {
                "id": c.id,
                "client_id": c.user_id,
                "consultation_date": c.consultation_date,
                "consultation_type": c.consultation_type,
                "fee_amount": float(c.fee_amount) if c.fee_amount else None,
            } for c in consultations
        ]

        # Get active clients
        active_clients = db.query(User).join(
            Case, Case.user_id == User.id
        ).filter(
            and_(Case.lawyer_id == lawyer_id, Case.status != "closed")
        ).distinct().limit(10).all()

        active_clients_data = [
            {
                "id": u.id,
                "name": u.username,
                "email": u.email,
                "phone": u.phone,
            } for u in active_clients
        ]

        # Get pending invoices
        pending_invoices = db.query(Invoice).filter(
            and_(Invoice.lawyer_id == lawyer_id, Invoice.status.in_(["draft", "issued"]))
        ).order_by(Invoice.due_date.asc()).limit(5).all()

        pending_invoices_data = [
            {
                "id": i.id,
                "invoice_number": i.invoice_number,
                "amount": float(i.total_amount),
                "status": i.status,
                "due_date": i.due_date,
                "citizen_id": i.citizen_id,
            } for i in pending_invoices
        ]

        # Get recent reviews
        reviews = db.query(LawyerReview).filter(
            LawyerReview.lawyer_id == lawyer_id
        ).order_by(LawyerReview.created_at.desc()).limit(5).all()

        recent_reviews = [
            {
                "id": r.id,
                "citizen_id": r.citizen_id,
                "rating": r.rating,
                "title": r.title,
                "created_at": r.created_at,
            } for r in reviews
        ]

        return {
            "stats": stats,
            "recent_cases": recent_cases,
            "upcoming_consultations": upcoming_consultations,
            "active_clients": active_clients_data,
            "pending_invoices": pending_invoices_data,
            "recent_reviews": recent_reviews,
        }

    @staticmethod
    def get_dashboard_stats(db: Session, lawyer_id: int) -> dict:
        """Get dashboard statistics"""

        # Case statistics
        total_clients = db.query(func.count(func.distinct(Case.user_id))).filter(
            Case.lawyer_id == lawyer_id
        ).scalar() or 0

        active_cases = db.query(Case).filter(
            and_(Case.lawyer_id == lawyer_id, Case.status.in_(["open", "in_progress"]))
        ).count()

        completed_cases = db.query(Case).filter(
            and_(Case.lawyer_id == lawyer_id, Case.status.in_(["closed", "resolved"]))
        ).count()

        # Consultation statistics
        total_consultations = db.query(Consultation).filter(
            Consultation.lawyer_id == lawyer_id
        ).count()

        now = datetime.now(timezone.utc)
        upcoming_consultations = db.query(Consultation).filter(
            and_(
                Consultation.lawyer_id == lawyer_id,
                Consultation.consultation_date >= now,
                Consultation.status == "scheduled"
            )
        ).count()

        # Earnings statistics
        total_earned = db.query(func.sum(Invoice.total_amount)).filter(
            and_(Invoice.lawyer_id == lawyer_id, Invoice.status == "paid")
        ).scalar()
        total_earned = float(total_earned) if total_earned else 0.0

        pending_invoices_count = db.query(Invoice).filter(
            and_(Invoice.lawyer_id == lawyer_id, Invoice.status.in_(["draft", "issued"]))
        ).count()

        unpaid_amount = db.query(func.sum(Invoice.total_amount)).filter(
            and_(
                Invoice.lawyer_id == lawyer_id,
                Invoice.status.in_(["issued", "overdue"])
            )
        ).scalar()
        unpaid_amount = float(unpaid_amount) if unpaid_amount else 0.0

        # Review statistics
        avg_rating = db.query(func.avg(LawyerReview.rating)).filter(
            LawyerReview.lawyer_id == lawyer_id
        ).scalar() or 0.0

        total_reviews = db.query(LawyerReview).filter(
            LawyerReview.lawyer_id == lawyer_id
        ).count()

        return {
            "total_clients": total_clients,
            "active_cases": active_cases,
            "completed_cases": completed_cases,
            "total_consultations": total_consultations,
            "upcoming_consultations": upcoming_consultations,
            "total_earned": total_earned,
            "pending_invoices": pending_invoices_count,
            "unpaid_invoices": unpaid_amount,
            "avg_satisfaction_rating": float(avg_rating),
            "total_reviews": total_reviews,
        }

    @staticmethod
    def get_cases_summary(db: Session, lawyer_id: int) -> dict:
        """Get detailed case summary"""
        cases = db.query(Case).filter(Case.lawyer_id == lawyer_id).all()

        status_breakdown = {}
        for case in cases:
            status = case.status
            if status not in status_breakdown:
                status_breakdown[status] = 0
            status_breakdown[status] += 1

        category_breakdown = {}
        for case in cases:
            category = case.category or "Uncategorized"
            if category not in category_breakdown:
                category_breakdown[category] = 0
            category_breakdown[category] += 1

        return {
            "total_cases": len(cases),
            "status_breakdown": status_breakdown,
            "category_breakdown": category_breakdown,
        }

    @staticmethod
    def get_earnings_summary(db: Session, lawyer_id: int) -> dict:
        """Get detailed earnings summary"""
        invoices = db.query(Invoice).filter(Invoice.lawyer_id == lawyer_id).all()

        total_issued = 0
        total_paid = 0
        total_overdue = 0

        for inv in invoices:
            if inv.status == "paid":
                total_paid += float(inv.total_amount)
            elif inv.status in ["issued", "draft"]:
                total_issued += float(inv.total_amount)
            elif inv.status == "overdue":
                total_overdue += float(inv.total_amount)

        return {
            "total_earned": total_paid,
            "pending_amount": total_issued,
            "overdue_amount": total_overdue,
            "total_invoices": len(invoices),
            "paid_invoices": len([i for i in invoices if i.status == "paid"]),
            "unpaid_invoices": len([i for i in invoices if i.status in ["issued", "draft", "overdue"]]),
        }

    @staticmethod
    def get_client_analytics(db: Session, lawyer_id: int) -> dict:
        """Get client-related analytics"""

        # Active clients
        active_clients = db.query(func.count(func.distinct(Case.user_id))).filter(
            and_(Case.lawyer_id == lawyer_id, Case.status != "closed")
        ).scalar() or 0

        # Total clients served
        total_clients = db.query(func.count(func.distinct(Case.user_id))).filter(
            Case.lawyer_id == lawyer_id
        ).scalar() or 0

        # Average cases per client
        avg_cases = total_clients and float(
            db.query(func.count(Case.id)).filter(
                Case.lawyer_id == lawyer_id
            ).scalar()
        ) / total_clients or 0

        # Client retention (completed cases / total clients)
        completed_cases = db.query(Case).filter(
            and_(Case.lawyer_id == lawyer_id, Case.status in ["closed", "resolved"])
        ).count()

        retention_rate = (
            (completed_cases / total_clients * 100) if total_clients > 0 else 0
        )

        return {
            "active_clients": active_clients,
            "total_clients": total_clients,
            "avg_cases_per_client": avg_cases,
            "completed_cases": completed_cases,
            "client_retention_rate": retention_rate,
        }

    @staticmethod
    def get_consultation_analytics(db: Session, lawyer_id: int) -> dict:
        """Get consultation analytics"""
        consultations = db.query(Consultation).filter(
            Consultation.lawyer_id == lawyer_id
        ).all()

        status_breakdown = {}
        for cons in consultations:
            status = cons.status
            if status not in status_breakdown:
                status_breakdown[status] = 0
            status_breakdown[status] += 1

        avg_fee = db.query(func.avg(Consultation.fee_amount)).filter(
            Consultation.lawyer_id == lawyer_id
        ).scalar()

        total_fee = db.query(func.sum(Consultation.fee_amount)).filter(
            Consultation.lawyer_id == lawyer_id
        ).scalar()

        return {
            "total_consultations": len(consultations),
            "status_breakdown": status_breakdown,
            "average_fee": float(avg_fee) if avg_fee else 0,
            "total_consultation_revenue": float(total_fee) if total_fee else 0,
        }

    @staticmethod
    def get_activity_summary(db: Session, lawyer_id: int, days: int = 30) -> dict:
        """Get activity summary for a period"""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

        cases_assigned = db.query(Case).filter(
            and_(Case.lawyer_id == lawyer_id, Case.created_at >= cutoff_date)
        ).count()

        consultations_completed = db.query(Consultation).filter(
            and_(
                Consultation.lawyer_id == lawyer_id,
                Consultation.status == "completed",
                Consultation.consultation_date >= cutoff_date
            )
        ).count()

        invoices_issued = db.query(Invoice).filter(
            and_(Invoice.lawyer_id == lawyer_id, Invoice.issued_at >= cutoff_date)
        ).count()

        reviews_received = db.query(LawyerReview).filter(
            and_(LawyerReview.lawyer_id == lawyer_id, LawyerReview.created_at >= cutoff_date)
        ).count()

        return {
            "period_days": days,
            "cases_assigned": cases_assigned,
            "consultations_completed": consultations_completed,
            "invoices_issued": invoices_issued,
            "reviews_received": reviews_received,
        }

    @staticmethod
    def get_performance_metrics(db: Session, lawyer_id: int) -> dict:
        """Get performance metrics"""
        reviews = db.query(LawyerReview).filter(
            LawyerReview.lawyer_id == lawyer_id
        ).all()

        if not reviews:
            return {
                "overall_rating": 0,
                "communication_rating": 0,
                "professionalism_rating": 0,
                "effectiveness_rating": 0,
                "total_reviews": 0,
            }

        communication_ratings = [r.communication_rating for r in reviews if r.communication_rating]
        professionalism_ratings = [r.professionalism_rating for r in reviews if r.professionalism_rating]
        effectiveness_ratings = [r.effectiveness_rating for r in reviews if r.effectiveness_rating]

        return {
            "overall_rating": sum(r.rating for r in reviews) / len(reviews),
            "communication_rating": (
                sum(communication_ratings) / len(communication_ratings)
                if communication_ratings else 0
            ),
            "professionalism_rating": (
                sum(professionalism_ratings) / len(professionalism_ratings)
                if professionalism_ratings else 0
            ),
            "effectiveness_rating": (
                sum(effectiveness_ratings) / len(effectiveness_ratings)
                if effectiveness_ratings else 0
            ),
            "total_reviews": len(reviews),
        }
