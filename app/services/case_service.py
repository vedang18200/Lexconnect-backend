"""Case service"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.database.models import Case, User, Lawyer, Payment
from app.api.schemas.case import CaseCreate, CaseUpdate
from fastapi import HTTPException, status

class CaseService:
    """Case business logic"""

    @staticmethod
    def create_case(db: Session, case: CaseCreate) -> Case:
        """Create a new case"""
        user = db.query(User).filter(User.id == case.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        db_case = Case(**case.model_dump())
        db.add(db_case)
        db.commit()
        db.refresh(db_case)
        return db_case

    @staticmethod
    def get_case_by_id(db: Session, case_id: int) -> Case:
        """Get case by ID"""
        db_case = db.query(Case).filter(Case.id == case_id).first()
        if not db_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found"
            )
        return db_case

    @staticmethod
    def update_case(db: Session, case_id: int, case_update: CaseUpdate) -> Case:
        """Update case"""
        db_case = CaseService.get_case_by_id(db, case_id)

        update_data = case_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_case, field, value)

        db.commit()
        db.refresh(db_case)
        return db_case

    @staticmethod
    def get_user_cases(db: Session, user_id: int, skip: int = 0, limit: int = 10):
        """Get all cases for a user"""
        return db.query(Case).filter(Case.user_id == user_id).offset(skip).limit(limit).all()

    @staticmethod
    def get_lawyer_cases(db: Session, lawyer_id: int, skip: int = 0, limit: int = 10):
        """Get all cases for a lawyer"""
        return db.query(Case).filter(Case.lawyer_id == lawyer_id).offset(skip).limit(limit).all()

    @staticmethod
    def get_all_cases(db: Session, skip: int = 0, limit: int = 10):
        """Get all cases"""
        return db.query(Case).offset(skip).limit(limit).all()

    @staticmethod
    def get_case_statistics(db: Session, user_id: int) -> dict:
        """Get case statistics for a citizen"""
        total_cases = db.query(Case).filter(Case.user_id == user_id).count()
        active_cases = db.query(Case).filter(
            and_(Case.user_id == user_id, Case.status.in_(["open", "in_progress", "active"]))
        ).count()
        pending_cases = db.query(Case).filter(
            and_(Case.user_id == user_id, Case.status == "pending")
        ).count()
        closed_cases = db.query(Case).filter(
            and_(Case.user_id == user_id, Case.status == "closed")
        ).count()
        resolved_cases = db.query(Case).filter(
            and_(Case.user_id == user_id, Case.status == "resolved")
        ).count()

        return {
            "total_cases": total_cases,
            "active_cases": active_cases,
            "pending_cases": pending_cases,
            "closed_cases": closed_cases,
            "resolved_cases": resolved_cases
        }

    @staticmethod
    def get_my_cases_detailed(
        db: Session,
        user_id: int,
        status_filter: str = None,
        priority_filter: str = None,
        search_query: str = None,
        skip: int = 0,
        limit: int = 10
    ) -> dict:
        """Get detailed cases for My Cases portal with filtering and search"""
        query = db.query(Case).filter(Case.user_id == user_id)

        # Apply status filter
        if status_filter and status_filter != "all":
            query = query.filter(Case.status == status_filter)

        # Apply priority filter
        if priority_filter and priority_filter != "all":
            query = query.filter(Case.priority == priority_filter)

        # Apply search query
        if search_query:
            search_pattern = f"%{search_query}%"
            query = query.filter(
                or_(
                    Case.title.ilike(search_pattern),
                    Case.case_number.ilike(search_pattern),
                    Case.category.ilike(search_pattern),
                    Case.description.ilike(search_pattern)
                )
            )

        total_count = query.count()
        cases = query.order_by(Case.updated_at.desc()).offset(skip).limit(limit).all()

        # Build detailed response for each case
        detailed_cases = []
        for case in cases:
            # Get lawyer info
            lawyer_info = None
            if case.lawyer_id:
                lawyer = db.query(Lawyer).filter(Lawyer.user_id == case.lawyer_id).first()
                if lawyer:
                    lawyer_info = {
                        "id": lawyer.id,
                        "user_id": lawyer.user_id,
                        "name": lawyer.user.username if lawyer.user else lawyer.name,
                        "email": lawyer.user.email if lawyer.user else lawyer.email,
                        "phone": lawyer.user.phone if lawyer.user else lawyer.phone,
                        "specialization": lawyer.specialization
                    }
                else:
                    # Fallback to User if Lawyer profile not found
                    lawyer_user = db.query(User).filter(User.id == case.lawyer_id).first()
                    if lawyer_user:
                        lawyer_info = {
                            "id": None,
                            "user_id": lawyer_user.id,
                            "name": lawyer_user.username,
                            "email": lawyer_user.email,
                            "phone": lawyer_user.phone,
                            "specialization": None
                        }

            # Get documents count
            documents_count = 0  # Will be calculated when Document model is added

            # Get updates count
            updates_count = 0  # Will be calculated when CaseUpdate model is added

            # Get legal fees - query ALL payments (both completed and pending)
            all_payments = db.query(Payment).filter(
                Payment.case_id == case.id
            ).all()

            # legal_fees_amount = total of all payments (completed + pending)
            legal_fees_amount = sum(float(payment.amount) for payment in all_payments) if all_payments else 0

            # legal_fees_paid = only completed payments
            legal_fees_paid = sum(float(payment.amount) for payment in all_payments if payment.status == "completed") if all_payments else 0

            detailed_cases.append({
                "id": case.id,
                "user_id": case.user_id,
                "lawyer_id": case.lawyer_id,
                "title": case.title,
                "description": case.description,
                "category": case.category,
                "status": case.status,
                "priority": case.priority,
                "case_number": case.case_number,
                "court_name": case.court_name,
                "hearing_date": case.hearing_date,
                "estimated_completion_date": case.estimated_completion_date,
                "case_progress": case.case_progress,
                "created_at": case.created_at,
                "updated_at": case.updated_at,
                "lawyer": lawyer_info,
                "documents_count": documents_count,
                "updates_count": updates_count,
                "legal_fees_amount": legal_fees_amount,
                "legal_fees_paid": legal_fees_paid
            })

        return {
            "total": total_count,
            "cases": detailed_cases,
            "page": skip // limit + 1 if limit > 0 else 1
        }
