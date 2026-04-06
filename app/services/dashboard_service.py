"""Dashboard service for citizen dashboard data"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timezone
from app.database.models import (
    Case, Consultation, Payment, LawyerReview, Notification, User, Lawyer, DocumentUpload
)
from app.services.citizen_service import CitizenService
from app.services.payment_service import PaymentService
from app.api.schemas.citizen import DashboardStats
from fastapi import HTTPException, status


class DashboardService:
    """Service for citizen dashboard"""

    @staticmethod
    def _format_consultation_code(consultation_id: int, created_at: datetime | None) -> str:
        """Build a stable display ID for consultation cards."""
        year = created_at.year if created_at else datetime.now(timezone.utc).year
        return f"CONS-{year}-{consultation_id:04d}"

    @staticmethod
    def _build_consultation_actions(consultation: Consultation, now: datetime) -> dict:
        """Derive CTA visibility from status, mode, and schedule."""
        mode = (consultation.consultation_type or "").lower()
        scheduled_for = consultation.consultation_date or consultation.scheduled_at
        is_scheduled = consultation.status == "scheduled"

        can_join_meeting = False
        if is_scheduled and scheduled_for:
            delta_minutes = (scheduled_for - now).total_seconds() / 60
            can_join_meeting = mode in {"video", "video call", "online"} and -15 <= delta_minutes <= 180

        return {
            "can_view_details": True,
            "can_join_meeting": can_join_meeting,
            "can_reschedule": is_scheduled,
            "can_cancel": is_scheduled,
        }

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
            and_(Case.user_id == citizen_id, Case.status.in_(["open", "in_progress", "active"]))
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
    def get_consultation_summary(
        db: Session,
        citizen_id: int,
        status_filter: str | None = None,
        mode_filter: str | None = None,
        query: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> dict:
        """Get detailed consultation summary with card-ready rows and filters."""
        now = datetime.now(timezone.utc)

        all_consultations = (
            db.query(Consultation)
            .filter(Consultation.user_id == citizen_id)
            .order_by(Consultation.consultation_date.desc().nullslast(), Consultation.id.desc())
            .all()
        )

        status_breakdown: dict[str, int] = {}
        type_breakdown: dict[str, int] = {}
        upcoming_count = 0
        completed_count = 0
        cancelled_count = 0

        for consultation in all_consultations:
            status_key = (consultation.status or "scheduled").lower()
            status_breakdown[status_key] = status_breakdown.get(status_key, 0) + 1

            type_key = (consultation.consultation_type or "General")
            type_breakdown[type_key] = type_breakdown.get(type_key, 0) + 1

            if status_key == "scheduled":
                upcoming_count += 1
            elif status_key == "completed":
                completed_count += 1
            elif status_key == "cancelled":
                cancelled_count += 1

        total_fee = db.query(func.sum(Consultation.fee_amount)).filter(
            Consultation.user_id == citizen_id
        ).scalar()

        filtered_consultations = all_consultations
        if status_filter and status_filter.lower() != "all":
            normalized_status = status_filter.lower()
            filtered_consultations = [
                c for c in filtered_consultations if (c.status or "").lower() == normalized_status
            ]

        if mode_filter and mode_filter.lower() != "all":
            normalized_mode = mode_filter.lower()
            filtered_consultations = [
                c for c in filtered_consultations if (c.consultation_type or "").lower() == normalized_mode
            ]

        if query:
            query_value = query.strip().lower()
            if query_value:
                matched_consultations: list[Consultation] = []
                for consultation in filtered_consultations:
                    lawyer = db.query(Lawyer).filter(Lawyer.user_id == consultation.lawyer_id).first()
                    lawyer_name = lawyer.name if lawyer else ""
                    case_title = consultation.case.title if consultation.case else ""
                    consultation_code = DashboardService._format_consultation_code(
                        consultation.id,
                        consultation.created_at,
                    )

                    if (
                        query_value in lawyer_name.lower()
                        or query_value in case_title.lower()
                        or query_value in consultation_code.lower()
                    ):
                        matched_consultations.append(consultation)
                filtered_consultations = matched_consultations

        total_filtered = len(filtered_consultations)
        paginated_consultations = filtered_consultations[skip: skip + limit]

        consultation_cards = []
        for consultation in paginated_consultations:
            lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == consultation.lawyer_id).first()
            lawyer_user = db.query(User).filter(User.id == consultation.lawyer_id).first()
            lawyer_name = (
                lawyer_profile.name
                if lawyer_profile and lawyer_profile.name
                else (lawyer_user.username if lawyer_user else "Lawyer")
            )
            initials = "".join(part[0] for part in lawyer_name.split()[:2]).upper() if lawyer_name else "LW"

            payment = (
                db.query(Payment)
                .filter(
                    and_(
                        Payment.citizen_id == citizen_id,
                        Payment.consultation_id == consultation.id,
                    )
                )
                .order_by(Payment.created_at.desc())
                .first()
            )

            attachments = []
            if consultation.case_id:
                documents = (
                    db.query(DocumentUpload)
                    .filter(
                        and_(
                            DocumentUpload.user_id == citizen_id,
                            DocumentUpload.case_id == consultation.case_id,
                        )
                    )
                    .order_by(DocumentUpload.uploaded_at.desc())
                    .limit(5)
                    .all()
                )
                attachments = [
                    {
                        "id": doc.id,
                        "name": doc.file_name,
                        "url": doc.file_url,
                        "mime_type": doc.mime_type,
                        "size": doc.file_size,
                    }
                    for doc in documents
                ]

            consultation_cards.append(
                {
                    "id": consultation.id,
                    "consultation_code": DashboardService._format_consultation_code(
                        consultation.id,
                        consultation.created_at,
                    ),
                    "status": consultation.status,
                    "consultation_mode": consultation.consultation_type or "General",
                    "scheduled_at": consultation.consultation_date or consultation.scheduled_at,
                    "duration_minutes": consultation.duration_minutes,
                    "note": consultation.notes,
                    "case": {
                        "id": consultation.case.id if consultation.case else None,
                        "title": consultation.case.title if consultation.case else None,
                        "category": consultation.case.category if consultation.case else None,
                    },
                    "lawyer": {
                        "id": consultation.lawyer_id,
                        "name": lawyer_name,
                        "initials": initials,
                        "specialization": lawyer_profile.specialization if lawyer_profile else None,
                        "rating": float(lawyer_profile.rating) if lawyer_profile and lawyer_profile.rating is not None else None,
                    },
                    "fee": {
                        "amount": float(consultation.fee_amount) if consultation.fee_amount is not None else None,
                        "currency": "INR",
                        "payment_status": payment.status if payment else "pending",
                    },
                    "attachments": attachments,
                    "actions": DashboardService._build_consultation_actions(consultation, now),
                }
            )

        return {
            "summary": {
                "total": len(all_consultations),
                "upcoming": upcoming_count,
                "completed": completed_count,
                "cancelled": cancelled_count,
            },
            "status_breakdown": status_breakdown,
            "type_breakdown": type_breakdown,
            "total_fee_spent": float(total_fee) if total_fee else 0.0,
            "filters": {
                "status": status_filter or "all",
                "mode": mode_filter or "all",
                "query": query or "",
            },
            "pagination": {
                "skip": skip,
                "limit": limit,
                "total": total_filtered,
                "returned": len(consultation_cards),
            },
            "consultations": consultation_cards,
        }

    @staticmethod
    def get_consultation_detail(db: Session, citizen_id: int, consultation_id: int) -> dict:
        """Get consultation detail payload for the View Details modal."""
        now = datetime.now(timezone.utc)

        consultation = (
            db.query(Consultation)
            .filter(
                and_(
                    Consultation.id == consultation_id,
                    Consultation.user_id == citizen_id,
                )
            )
            .first()
        )
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Consultation not found",
            )

        lawyer_profile = db.query(Lawyer).filter(Lawyer.user_id == consultation.lawyer_id).first()
        lawyer_user = db.query(User).filter(User.id == consultation.lawyer_id).first()
        lawyer_name = (
            lawyer_profile.name
            if lawyer_profile and lawyer_profile.name
            else (lawyer_user.username if lawyer_user else "Lawyer")
        )
        initials = "".join(part[0] for part in lawyer_name.split()[:2]).upper() if lawyer_name else "LW"

        payment = (
            db.query(Payment)
            .filter(
                and_(
                    Payment.citizen_id == citizen_id,
                    Payment.consultation_id == consultation.id,
                )
            )
            .order_by(Payment.created_at.desc())
            .first()
        )

        documents = []
        if consultation.case_id:
            case_documents = (
                db.query(DocumentUpload)
                .filter(
                    and_(
                        DocumentUpload.user_id == citizen_id,
                        DocumentUpload.case_id == consultation.case_id,
                    )
                )
                .order_by(DocumentUpload.uploaded_at.desc())
                .all()
            )
            documents = [
                {
                    "id": doc.id,
                    "name": doc.file_name,
                    "url": doc.file_url,
                    "mime_type": doc.mime_type,
                    "size": doc.file_size,
                    "uploaded_at": doc.uploaded_at,
                }
                for doc in case_documents
            ]

        consultation_mode = consultation.consultation_type or "General"
        mode_normalized = consultation_mode.lower()
        meeting_link = None
        if mode_normalized in {"video", "video call", "online"}:
            meeting_link = f"/consultations/{consultation.id}/join"

        return {
            "id": consultation.id,
            "consultation_code": DashboardService._format_consultation_code(
                consultation.id,
                consultation.created_at,
            ),
            "status": consultation.status,
            "lawyer_information": {
                "id": consultation.lawyer_id,
                "initials": initials,
                "name": lawyer_name,
                "specialization": lawyer_profile.specialization if lawyer_profile else None,
                "rating": float(lawyer_profile.rating) if lawyer_profile and lawyer_profile.rating is not None else None,
            },
            "consultation_details": {
                "date_time": consultation.consultation_date or consultation.scheduled_at,
                "duration_minutes": consultation.duration_minutes,
                "mode": consultation_mode,
                "fee": {
                    "amount": float(consultation.fee_amount) if consultation.fee_amount is not None else None,
                    "currency": "INR",
                },
                "related_case": {
                    "id": consultation.case.id if consultation.case else None,
                    "title": consultation.case.title if consultation.case else None,
                },
                "meeting_link": meeting_link,
            },
            "preparation_notes": consultation.notes,
            "documents": documents,
            "payment_information": {
                "consultation_fee": float(consultation.fee_amount) if consultation.fee_amount is not None else None,
                "currency": "INR",
                "status": payment.status if payment else "pending",
            },
            "actions": DashboardService._build_consultation_actions(consultation, now),
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
