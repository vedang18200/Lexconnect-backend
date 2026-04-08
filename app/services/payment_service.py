"""Payment service for managing transactions"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import HTTPException, status
from datetime import datetime, timezone, date, time
from decimal import Decimal
from uuid import uuid4
from app.database.models import Payment, Consultation, Case, User


class PaymentService:
    """Service for managing payments"""

    @staticmethod
    def create_payment(
        db: Session,
        citizen_id: int,
        lawyer_id: int,
        amount: Decimal,
        payment_method: str,
        consultation_id: int = None,
        case_id: int = None,
        description: str = None,
    ) -> Payment:
        """Create a new payment"""
        # Verify lawyer exists
        lawyer = db.query(User).filter(
            and_(User.id == lawyer_id, User.user_type == "lawyer")
        ).first()
        if not lawyer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer not found"
            )

        # Verify consultation exists if provided
        if consultation_id:
            consultation = db.query(Consultation).filter(Consultation.id == consultation_id).first()
            if not consultation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Consultation not found"
                )
            if consultation.user_id != citizen_id or consultation.lawyer_id != lawyer_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Invalid consultation for payment"
                )

        # Verify case exists if provided
        if case_id:
            case = db.query(Case).filter(Case.id == case_id).first()
            if not case:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Case not found"
                )
            if case.user_id != citizen_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have access to this case"
                )

        transaction_id = f"TXN_{uuid4().hex[:12].upper()}"

        db_payment = Payment(
            citizen_id=citizen_id,
            lawyer_id=lawyer_id,
            consultation_id=consultation_id,
            case_id=case_id,
            amount=amount,
            payment_method=payment_method,
            description=description,
            transaction_id=transaction_id,
            status="pending",
        )
        db.add(db_payment)
        db.commit()
        db.refresh(db_payment)
        return db_payment

    @staticmethod
    def get_payment(db: Session, payment_id: int, user_id: int) -> Payment:
        """Get a specific payment"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        # Check if user has access to this payment
        if payment.citizen_id != user_id and payment.lawyer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this payment"
            )

        return payment

    @staticmethod
    def get_citizen_payments(db: Session, citizen_id: int, skip: int = 0, limit: int = 10):
        """Get all payments made by a citizen"""
        total = db.query(Payment).filter(Payment.citizen_id == citizen_id).count()
        payments = (
            db.query(Payment)
            .filter(Payment.citizen_id == citizen_id)
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {"total": total, "payments": payments}

    @staticmethod
    def get_lawyer_payments(db: Session, lawyer_id: int, skip: int = 0, limit: int = 10):
        """Get all payments received by a lawyer"""
        total = db.query(Payment).filter(
            and_(Payment.lawyer_id == lawyer_id, Payment.status == "completed")
        ).count()
        payments = (
            db.query(Payment)
            .filter(and_(Payment.lawyer_id == lawyer_id, Payment.status == "completed"))
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return {"total": total, "payments": payments}

    @staticmethod
    def confirm_payment(db: Session, payment_id: int, user_id: int) -> Payment:
        """Confirm payment has been made (mark as completed)"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        if payment.citizen_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the payer can confirm this payment"
            )

        if payment.status == "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment already completed"
            )

        payment.status = "completed"
        payment.paid_at = datetime.now(timezone.utc)
        payment.confirmed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def fail_payment(db: Session, payment_id: int, reason: str = None) -> Payment:
        """Mark payment as failed"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        payment.status = "failed"
        if reason:
            payment.description = f"Failed: {reason}"
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def refund_payment(db: Session, payment_id: int, user_id: int) -> Payment:
        """Refund a payment"""
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        if payment.citizen_id != user_id and payment.lawyer_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to refund this payment"
            )

        if payment.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only completed payments can be refunded"
            )

        payment.status = "refunded"
        db.commit()
        db.refresh(payment)
        return payment

    @staticmethod
    def get_lawyer_earnings(db: Session, lawyer_id: int) -> dict:
        """Get earnings summary for a lawyer"""
        completed_payments = db.query(Payment).filter(
            and_(Payment.lawyer_id == lawyer_id, Payment.status == "completed")
        ).all()

        total_earnings = sum(p.amount for p in completed_payments)
        total_transactions = len(completed_payments)

        return {
            "total_earnings": total_earnings,
            "total_transactions": total_transactions,
            "payments": completed_payments
        }

    @staticmethod
    def get_citizen_spending(db: Session, citizen_id: int) -> dict:
        """Get spending summary for a citizen"""
        completed_payments = db.query(Payment).filter(
            and_(Payment.citizen_id == citizen_id, Payment.status == "completed")
        ).all()

        total_spent = sum(p.amount for p in completed_payments)
        total_transactions = len(completed_payments)
        lawyers_paid = len(set(p.lawyer_id for p in completed_payments))

        return {
            "total_spent": total_spent,
            "total_transactions": total_transactions,
            "lawyers_paid": lawyers_paid,
            "payments": completed_payments
        }

    @staticmethod
    def get_billing_history(
        db: Session,
        citizen_id: int,
        skip: int = 0,
        limit: int = 10,
        status_filter: str | None = None,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> dict:
        """Get billing history for a citizen profile tab with summary and filters."""
        query = db.query(Payment).filter(Payment.citizen_id == citizen_id)

        if status_filter:
            query = query.filter(Payment.status == status_filter.lower())

        if from_date:
            start_dt = datetime.combine(from_date, time.min).replace(tzinfo=timezone.utc)
            query = query.filter(Payment.created_at >= start_dt)

        if to_date:
            end_dt = datetime.combine(to_date, time.max).replace(tzinfo=timezone.utc)
            query = query.filter(Payment.created_at <= end_dt)

        total = query.count()
        payments = (
            query
            .order_by(Payment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        completed_query = db.query(Payment).filter(
            Payment.citizen_id == citizen_id,
            Payment.status == "completed",
        )

        if from_date:
            start_dt = datetime.combine(from_date, time.min).replace(tzinfo=timezone.utc)
            completed_query = completed_query.filter(Payment.created_at >= start_dt)
        if to_date:
            end_dt = datetime.combine(to_date, time.max).replace(tzinfo=timezone.utc)
            completed_query = completed_query.filter(Payment.created_at <= end_dt)

        total_spent = sum(float(payment.amount) for payment in completed_query.all())

        items = []
        for payment in payments:
            lawyer = db.query(User).filter(User.id == payment.lawyer_id).first()
            lawyer_name = lawyer.username if lawyer else "Lawyer"
            title = payment.description or f"Payment - {lawyer_name}"
            items.append(
                {
                    "id": payment.id,
                    "title": title,
                    "date": payment.created_at,
                    "payment_method": payment.payment_method,
                    "transaction_id": payment.transaction_id,
                    "amount": float(payment.amount),
                    "currency": "INR",
                    "status": payment.status.title(),
                }
            )

        return {
            "items": items,
            "total": total,
            "summary": {
                "total_spent": total_spent,
                "currency": "INR",
            },
        }
