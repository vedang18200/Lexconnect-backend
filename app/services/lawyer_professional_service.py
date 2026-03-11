"""Lawyer professional features service"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from fastapi import HTTPException, status
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from app.database.models import (
    LawyerCredential, LawyerAvailability, Invoice, DocumentTemplate,
    CaseNote, User, Case, Consultation, LawyerReview, Payment
)
from app.api.schemas.lawyer_professional import (
    LawyerCredentialCreate, LawyerAvailabilityCreate, InvoiceCreate,
    DocumentTemplateCreate, CaseNoteCreate
)


class LawyerCredentialService:
    """Service for managing lawyer credentials"""

    @staticmethod
    def create_or_update_credential(
        db: Session, lawyer_id: int, credential: LawyerCredentialCreate
    ) -> LawyerCredential:
        """Create or update lawyer credentials"""
        existing = db.query(LawyerCredential).filter(
            LawyerCredential.lawyer_id == lawyer_id
        ).first()

        if existing:
            for field, value in credential.model_dump().items():
                if value is not None:
                    setattr(existing, field, value)
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            db_credential = LawyerCredential(
                lawyer_id=lawyer_id,
                **credential.model_dump()
            )
            db.add(db_credential)
            db.commit()
            db.refresh(db_credential)
            return db_credential

    @staticmethod
    def get_credential(db: Session, lawyer_id: int) -> LawyerCredential:
        """Get lawyer credentials"""
        credential = db.query(LawyerCredential).filter(
            LawyerCredential.lawyer_id == lawyer_id
        ).first()
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lawyer credentials not found"
            )
        return credential

    @staticmethod
    def verify_credential(db: Session, lawyer_id: int) -> LawyerCredential:
        """Verify lawyer credentials (admin only)"""
        credential = LawyerCredentialService.get_credential(db, lawyer_id)
        credential.is_verified = True
        credential.verified_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(credential)
        return credential


class LawyerAvailabilityService:
    """Service for managing lawyer availability"""

    @staticmethod
    def create_availability(
        db: Session, lawyer_id: int, availability: LawyerAvailabilityCreate
    ) -> LawyerAvailability:
        """Create availability slot"""
        db_availability = LawyerAvailability(
            lawyer_id=lawyer_id,
            **availability.model_dump()
        )
        db.add(db_availability)
        db.commit()
        db.refresh(db_availability)
        return db_availability

    @staticmethod
    def get_availability_by_day(db: Session, lawyer_id: int, day_of_week: int):
        """Get availability for a specific day"""
        return db.query(LawyerAvailability).filter(
            and_(
                LawyerAvailability.lawyer_id == lawyer_id,
                LawyerAvailability.day_of_week == day_of_week,
                LawyerAvailability.is_available == True
            )
        ).all()

    @staticmethod
    def get_all_availability(db: Session, lawyer_id: int):
        """Get all availability slots"""
        return db.query(LawyerAvailability).filter(
            LawyerAvailability.lawyer_id == lawyer_id
        ).all()

    @staticmethod
    def update_availability(
        db: Session, availability_id: int, lawyer_id: int, update_data: dict
    ) -> LawyerAvailability:
        """Update availability slot"""
        availability = db.query(LawyerAvailability).filter(
            and_(
                LawyerAvailability.id == availability_id,
                LawyerAvailability.lawyer_id == lawyer_id
            )
        ).first()

        if not availability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Availability slot not found"
            )

        for field, value in update_data.items():
            if value is not None and hasattr(availability, field):
                setattr(availability, field, value)

        availability.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(availability)
        return availability

    @staticmethod
    def delete_availability(
        db: Session, availability_id: int, lawyer_id: int
    ) -> None:
        """Delete availability slot"""
        availability = db.query(LawyerAvailability).filter(
            and_(
                LawyerAvailability.id == availability_id,
                LawyerAvailability.lawyer_id == lawyer_id
            )
        ).first()

        if not availability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Availability slot not found"
            )

        db.delete(availability)
        db.commit()


class InvoiceService:
    """Service for managing invoices"""

    @staticmethod
    def create_invoice(
        db: Session, lawyer_id: int, invoice: InvoiceCreate
    ) -> Invoice:
        """Create an invoice"""
        # Generate invoice number
        invoice_number = f"INV-{uuid4().hex[:8].upper()}"

        db_invoice = Invoice(
            lawyer_id=lawyer_id,
            invoice_number=invoice_number,
            **invoice.model_dump()
        )
        db.add(db_invoice)
        db.commit()
        db.refresh(db_invoice)
        return db_invoice

    @staticmethod
    def get_invoice(db: Session, invoice_id: int, lawyer_id: int) -> Invoice:
        """Get invoice"""
        invoice = db.query(Invoice).filter(
            and_(
                Invoice.id == invoice_id,
                Invoice.lawyer_id == lawyer_id
            )
        ).first()

        if not invoice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invoice not found"
            )
        return invoice

    @staticmethod
    def get_invoices_by_lawyer(
        db: Session, lawyer_id: int, skip: int = 0, limit: int = 10
    ):
        """Get all invoices for a lawyer"""
        total = db.query(Invoice).filter(Invoice.lawyer_id == lawyer_id).count()
        invoices = db.query(Invoice).filter(
            Invoice.lawyer_id == lawyer_id
        ).offset(skip).limit(limit).all()

        return {"total": total, "invoices": invoices}

    @staticmethod
    def get_invoices_by_status(
        db: Session, lawyer_id: int, status: str, skip: int = 0, limit: int = 10
    ):
        """Get invoices by status"""
        total = db.query(Invoice).filter(
            and_(Invoice.lawyer_id == lawyer_id, Invoice.status == status)
        ).count()
        invoices = db.query(Invoice).filter(
            and_(Invoice.lawyer_id == lawyer_id, Invoice.status == status)
        ).offset(skip).limit(limit).all()

        return {"total": total, "invoices": invoices}

    @staticmethod
    def mark_invoice_paid(db: Session, invoice_id: int, lawyer_id: int) -> Invoice:
        """Mark invoice as paid"""
        invoice = InvoiceService.get_invoice(db, invoice_id, lawyer_id)

        invoice.status = "paid"
        invoice.paid_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def issue_invoice(db: Session, invoice_id: int, lawyer_id: int) -> Invoice:
        """Issue an invoice"""
        invoice = InvoiceService.get_invoice(db, invoice_id, lawyer_id)

        invoice.status = "issued"
        invoice.issued_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def get_earnings_summary(db: Session, lawyer_id: int) -> dict:
        """Get earnings summary for a lawyer"""
        paid_invoices = db.query(func.sum(Invoice.total_amount)).filter(
            and_(Invoice.lawyer_id == lawyer_id, Invoice.status == "paid")
        ).scalar()

        unpaid_invoices = db.query(func.sum(Invoice.total_amount)).filter(
            and_(
                Invoice.lawyer_id == lawyer_id,
                Invoice.status.in_(["issued", "overdue"])
            )
        ).scalar()

        return {
            "total_earned": float(paid_invoices) if paid_invoices else 0.0,
            "pending_amount": float(unpaid_invoices) if unpaid_invoices else 0.0,
        }


class DocumentTemplateService:
    """Service for managing document templates"""

    @staticmethod
    def create_template(
        db: Session, lawyer_id: int, template: DocumentTemplateCreate
    ) -> DocumentTemplate:
        """Create a document template"""
        db_template = DocumentTemplate(
            lawyer_id=lawyer_id,
            **template.model_dump()
        )
        db.add(db_template)
        db.commit()
        db.refresh(db_template)
        return db_template

    @staticmethod
    def get_template(db: Session, template_id: int, lawyer_id: int) -> DocumentTemplate:
        """Get a template"""
        template = db.query(DocumentTemplate).filter(
            DocumentTemplate.id == template_id
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        # Check if user has access
        if template.lawyer_id != lawyer_id and not template.is_public:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this template"
            )

        return template

    @staticmethod
    def get_templates_by_lawyer(
        db: Session, lawyer_id: int, skip: int = 0, limit: int = 10
    ):
        """Get all templates for a lawyer"""
        total = db.query(DocumentTemplate).filter(
            DocumentTemplate.lawyer_id == lawyer_id
        ).count()
        templates = db.query(DocumentTemplate).filter(
            DocumentTemplate.lawyer_id == lawyer_id
        ).offset(skip).limit(limit).all()

        return {"total": total, "templates": templates}

    @staticmethod
    def get_templates_by_type(
        db: Session, template_type: str, lawyer_id: int = None, skip: int = 0, limit: int = 10
    ):
        """Get templates by type"""
        query = db.query(DocumentTemplate).filter(
            or_(
                DocumentTemplate.template_type == template_type,
                DocumentTemplate.is_public == True
            )
        )

        if lawyer_id:
            query = query.filter(
                or_(
                    DocumentTemplate.lawyer_id == lawyer_id,
                    DocumentTemplate.is_public == True
                )
            )

        total = query.count()
        templates = query.offset(skip).limit(limit).all()

        return {"total": total, "templates": templates}

    @staticmethod
    def update_template(
        db: Session, template_id: int, lawyer_id: int, update_data: dict
    ) -> DocumentTemplate:
        """Update a template"""
        template = db.query(DocumentTemplate).filter(
            and_(
                DocumentTemplate.id == template_id,
                DocumentTemplate.lawyer_id == lawyer_id
            )
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        for field, value in update_data.items():
            if value is not None and hasattr(template, field):
                setattr(template, field, value)

        db.commit()
        db.refresh(template)
        return template

    @staticmethod
    def delete_template(db: Session, template_id: int, lawyer_id: int) -> None:
        """Delete a template"""
        template = db.query(DocumentTemplate).filter(
            and_(
                DocumentTemplate.id == template_id,
                DocumentTemplate.lawyer_id == lawyer_id
            )
        ).first()

        if not template:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Template not found"
            )

        db.delete(template)
        db.commit()

    @staticmethod
    def increment_usage(db: Session, template_id: int) -> None:
        """Increment template usage count"""
        template = db.query(DocumentTemplate).filter(
            DocumentTemplate.id == template_id
        ).first()

        if template:
            template.usage_count += 1
            db.commit()


class CaseNoteService:
    """Service for managing case notes"""

    @staticmethod
    def create_note(
        db: Session, lawyer_id: int, note: CaseNoteCreate
    ) -> CaseNote:
        """Create a case note"""
        # Verify lawyer has access to the case
        case = db.query(Case).filter(Case.id == note.case_id).first()
        if not case or case.lawyer_id != lawyer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this case"
            )

        db_note = CaseNote(
            lawyer_id=lawyer_id,
            **note.model_dump()
        )
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        return db_note

    @staticmethod
    def get_case_notes(
        db: Session, case_id: int, lawyer_id: int, skip: int = 0, limit: int = 10
    ):
        """Get all notes for a case"""
        # Verify lawyer has access to the case
        case = db.query(Case).filter(Case.id == case_id).first()
        if not case or case.lawyer_id != lawyer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this case"
            )

        total = db.query(CaseNote).filter(CaseNote.case_id == case_id).count()
        notes = db.query(CaseNote).filter(
            CaseNote.case_id == case_id
        ).order_by(CaseNote.created_at.desc()).offset(skip).limit(limit).all()

        return {"total": total, "notes": notes}

    @staticmethod
    def get_note(db: Session, note_id: int, lawyer_id: int) -> CaseNote:
        """Get a specific note"""
        note = db.query(CaseNote).filter(CaseNote.id == note_id).first()

        if not note:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Note not found"
            )

        if note.lawyer_id != lawyer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this note"
            )

        return note

    @staticmethod
    def update_note(
        db: Session, note_id: int, lawyer_id: int, update_data: dict
    ) -> CaseNote:
        """Update a note"""
        note = CaseNoteService.get_note(db, note_id, lawyer_id)

        for field, value in update_data.items():
            if value is not None and hasattr(note, field):
                setattr(note, field, value)

        note.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def mark_note_complete(db: Session, note_id: int, lawyer_id: int) -> CaseNote:
        """Mark note as complete"""
        note = CaseNoteService.get_note(db, note_id, lawyer_id)

        note.is_completed = True
        note.completed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(note)
        return note

    @staticmethod
    def delete_note(db: Session, note_id: int, lawyer_id: int) -> None:
        """Delete a note"""
        note = CaseNoteService.get_note(db, note_id, lawyer_id)
        db.delete(note)
        db.commit()

    @staticmethod
    def get_pending_notes(db: Session, lawyer_id: int):
        """Get all pending notes for a lawyer"""
        return db.query(CaseNote).filter(
            and_(
                CaseNote.lawyer_id == lawyer_id,
                CaseNote.is_completed == False
            )
        ).order_by(CaseNote.due_date.asc()).all()
