"""Lawyer professional endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.core.security import verify_token
from fastapi.security import HTTPAuthorizationCredentials
from app.services.lawyer_professional_service import (
    LawyerCredentialService, LawyerAvailabilityService,
    InvoiceService, DocumentTemplateService, CaseNoteService
)
from app.services.lawyer_dashboard_service import LawyerDashboardService
from app.api.schemas.lawyer_professional import (
    LawyerCredentialResponse, LawyerCredentialCreate,
    LawyerAvailabilityResponse, LawyerAvailabilityCreate,
    InvoiceResponse, InvoiceCreate,
    DocumentTemplateResponse, DocumentTemplateCreate,
    CaseNoteResponse, CaseNoteCreate,
    LawyerDashboardResponse
)
from typing import List, Optional

router = APIRouter(prefix="/lawyers/professional", tags=["Lawyer Professional"])


# === CREDENTIALS ENDPOINTS ===

@router.post("/credentials", response_model=LawyerCredentialResponse)
def create_or_update_credentials(
    credential: LawyerCredentialCreate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create or update lawyer credentials"""
    user_id = int(credentials.credentials.split('.')[-1])
    db_credential = LawyerCredentialService.create_or_update_credential(
        db, user_id, credential
    )
    return db_credential


@router.get("/credentials", response_model=LawyerCredentialResponse)
def get_credentials(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get lawyer credentials"""
    user_id = int(credentials.credentials.split('.')[-1])
    credential = LawyerCredentialService.get_credential(db, user_id)
    return credential


# === AVAILABILITY ENDPOINTS ===

@router.post("/availability", response_model=LawyerAvailabilityResponse)
def create_availability(
    availability: LawyerAvailabilityCreate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create availability slot"""
    user_id = int(credentials.credentials.split('.')[-1])
    db_availability = LawyerAvailabilityService.create_availability(
        db, user_id, availability
    )
    return db_availability


@router.get("/availability", response_model=List[LawyerAvailabilityResponse])
def get_all_availability(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all availability slots"""
    user_id = int(credentials.credentials.split('.')[-1])
    availabilities = LawyerAvailabilityService.get_all_availability(db, user_id)
    return availabilities


@router.get("/availability/day/{day_of_week}", response_model=List[LawyerAvailabilityResponse])
def get_availability_by_day(
    day_of_week: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get availability for a specific day"""
    user_id = int(credentials.credentials.split('.')[-1])
    availabilities = LawyerAvailabilityService.get_availability_by_day(
        db, user_id, day_of_week
    )
    return availabilities


@router.put("/availability/{availability_id}", response_model=LawyerAvailabilityResponse)
def update_availability(
    availability_id: int,
    update_data: dict,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update availability slot"""
    user_id = int(credentials.credentials.split('.')[-1])
    availability = LawyerAvailabilityService.update_availability(
        db, availability_id, user_id, update_data
    )
    return availability


@router.delete("/availability/{availability_id}")
def delete_availability(
    availability_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete availability slot"""
    user_id = int(credentials.credentials.split('.')[-1])
    LawyerAvailabilityService.delete_availability(db, availability_id, user_id)
    return {"message": "Availability slot deleted successfully"}


# === INVOICE ENDPOINTS ===

@router.post("/invoices", response_model=InvoiceResponse)
def create_invoice(
    invoice: InvoiceCreate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create an invoice"""
    user_id = int(credentials.credentials.split('.')[-1])
    db_invoice = InvoiceService.create_invoice(db, user_id, invoice)
    return db_invoice


@router.get("/invoices", response_model=dict)
def list_invoices(
    skip: int = Query(0),
    limit: int = Query(10),
    status: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List invoices"""
    user_id = int(credentials.credentials.split('.')[-1])
    if status:
        return InvoiceService.get_invoices_by_status(db, user_id, status, skip, limit)
    else:
        return InvoiceService.get_invoices_by_lawyer(db, user_id, skip, limit)


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get invoice details"""
    user_id = int(credentials.credentials.split('.')[-1])
    invoice = InvoiceService.get_invoice(db, invoice_id, user_id)
    return invoice


@router.post("/invoices/{invoice_id}/issue", response_model=InvoiceResponse)
def issue_invoice(
    invoice_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Issue an invoice"""
    user_id = int(credentials.credentials.split('.')[-1])
    invoice = InvoiceService.issue_invoice(db, invoice_id, user_id)
    return invoice


@router.post("/invoices/{invoice_id}/mark-paid", response_model=InvoiceResponse)
def mark_invoice_paid(
    invoice_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Mark invoice as paid"""
    user_id = int(credentials.credentials.split('.')[-1])
    invoice = InvoiceService.mark_invoice_paid(db, invoice_id, user_id)
    return invoice


@router.get("/earnings-summary")
def get_earnings_summary(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get earnings summary"""
    user_id = int(credentials.credentials.split('.')[-1])
    return InvoiceService.get_earnings_summary(db, user_id)


# === DOCUMENT TEMPLATES ENDPOINTS ===

@router.post("/templates", response_model=DocumentTemplateResponse)
def create_template(
    template: DocumentTemplateCreate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create document template"""
    user_id = int(credentials.credentials.split('.')[-1])
    db_template = DocumentTemplateService.create_template(db, user_id, template)
    return db_template


@router.get("/templates", response_model=dict)
def list_templates(
    skip: int = Query(0),
    limit: int = Query(10),
    template_type: Optional[str] = None,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """List templates"""
    user_id = int(credentials.credentials.split('.')[-1])
    if template_type:
        return DocumentTemplateService.get_templates_by_type(
            db, template_type, user_id, skip, limit
        )
    else:
        return DocumentTemplateService.get_templates_by_lawyer(db, user_id, skip, limit)


@router.get("/templates/{template_id}", response_model=DocumentTemplateResponse)
def get_template(
    template_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get template details"""
    user_id = int(credentials.credentials.split('.')[-1])
    template = DocumentTemplateService.get_template(db, template_id, user_id)
    return template


@router.put("/templates/{template_id}", response_model=DocumentTemplateResponse)
def update_template(
    template_id: int,
    update_data: dict,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update template"""
    user_id = int(credentials.credentials.split('.')[-1])
    template = DocumentTemplateService.update_template(db, template_id, user_id, update_data)
    return template


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete template"""
    user_id = int(credentials.credentials.split('.')[-1])
    DocumentTemplateService.delete_template(db, template_id, user_id)
    return {"message": "Template deleted successfully"}


# === CASE NOTES ENDPOINTS ===

@router.post("/case-notes", response_model=CaseNoteResponse)
def create_case_note(
    note: CaseNoteCreate,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Create case note"""
    user_id = int(credentials.credentials.split('.')[-1])
    db_note = CaseNoteService.create_note(db, user_id, note)
    return db_note


@router.get("/case-notes/case/{case_id}", response_model=dict)
def get_case_notes(
    case_id: int,
    skip: int = Query(0),
    limit: int = Query(10),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get case notes"""
    user_id = int(credentials.credentials.split('.')[-1])
    return CaseNoteService.get_case_notes(db, case_id, user_id, skip, limit)


@router.get("/case-notes/{note_id}", response_model=CaseNoteResponse)
def get_case_note(
    note_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get case note details"""
    user_id = int(credentials.credentials.split('.')[-1])
    note = CaseNoteService.get_note(db, note_id, user_id)
    return note


@router.put("/case-notes/{note_id}", response_model=CaseNoteResponse)
def update_case_note(
    note_id: int,
    update_data: dict,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Update case note"""
    user_id = int(credentials.credentials.split('.')[-1])
    note = CaseNoteService.update_note(db, note_id, user_id, update_data)
    return note


@router.post("/case-notes/{note_id}/complete", response_model=CaseNoteResponse)
def mark_note_complete(
    note_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Mark case note as complete"""
    user_id = int(credentials.credentials.split('.')[-1])
    note = CaseNoteService.mark_note_complete(db, note_id, user_id)
    return note


@router.delete("/case-notes/{note_id}")
def delete_case_note(
    note_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Delete case note"""
    user_id = int(credentials.credentials.split('.')[-1])
    CaseNoteService.delete_note(db, note_id, user_id)
    return {"message": "Case note deleted successfully"}


@router.get("/case-notes/pending")
def get_pending_notes(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get all pending case notes"""
    user_id = int(credentials.credentials.split('.')[-1])
    notes = CaseNoteService.get_pending_notes(db, user_id)
    return [{"id": n.id, "case_id": n.case_id, "content": n.content, "due_date": n.due_date} for n in notes]


# === DASHBOARD ENDPOINTS ===

@router.get("/dashboard", response_model=dict)
def get_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get lawyer dashboard"""
    user_id = int(credentials.credentials.split('.')[-1])
    dashboard_data = LawyerDashboardService.get_dashboard_data(db, user_id)
    return dashboard_data


@router.get("/dashboard/stats")
def get_dashboard_stats(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    user_id = int(credentials.credentials.split('.')[-1])
    stats = LawyerDashboardService.get_dashboard_stats(db, user_id)
    return stats


@router.get("/dashboard/cases-summary")
def get_cases_summary(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get case summary"""
    user_id = int(credentials.credentials.split('.')[-1])
    return LawyerDashboardService.get_cases_summary(db, user_id)


@router.get("/dashboard/earnings-summary")
def get_earnings_summary_dashboard(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get earnings summary"""
    user_id = int(credentials.credentials.split('.')[-1])
    return LawyerDashboardService.get_earnings_summary(db, user_id)


@router.get("/dashboard/clients-analytics")
def get_clients_analytics(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get client analytics"""
    user_id = int(credentials.credentials.split('.')[-1])
    return LawyerDashboardService.get_client_analytics(db, user_id)


@router.get("/dashboard/consultations-analytics")
def get_consultations_analytics(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get consultation analytics"""
    user_id = int(credentials.credentials.split('.')[-1])
    return LawyerDashboardService.get_consultation_analytics(db, user_id)


@router.get("/dashboard/activity")
def get_activity_summary(
    days: int = Query(30, ge=1, le=365),
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get activity summary"""
    user_id = int(credentials.credentials.split('.')[-1])
    return LawyerDashboardService.get_activity_summary(db, user_id, days)


@router.get("/dashboard/performance")
def get_performance_metrics(
    credentials: HTTPAuthorizationCredentials = Depends(verify_token),
    db: Session = Depends(get_db)
):
    """Get performance metrics"""
    user_id = int(credentials.credentials.split('.')[-1])
    return LawyerDashboardService.get_performance_metrics(db, user_id)
