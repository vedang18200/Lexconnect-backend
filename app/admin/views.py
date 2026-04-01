"""Admin panel views for all models.

N+1 prevention strategy:
  - Relationship attributes listed in column_list trigger automatic selectinload
    inside sqladmin – one extra IN-query per relationship, not one per row.
  - column_formatters only access attributes that are already loaded via the
    selectinload, so they never fire additional queries.
"""
from typing import Any
from starlette.requests import Request
from sqladmin import ModelView
from sqladmin.filters import BooleanFilter, StaticValuesFilter, AllUniqueStringValuesFilter
from app.database.models import (
    User, Lawyer, Case, Consultation, DirectMessage, ChatMessage,
    CitizenProfile, DocumentUpload, LawyerReview, Payment, TwoFactorAuth,
    Notification, LawyerCredential, LawyerAvailability, Invoice,
    DocumentTemplate, CaseNote, Agency, SocialWorkerProfile, Referral,
)
from app.core.security import get_password_hash


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _user_label(user) -> str:
    if user is None:
        return "—"
    return f"{user.username} ({user.user_type})"


# ══════════════════════════════════════════════
# USERS & PROFILES
# ══════════════════════════════════════════════

class UserAdmin(ModelView, model=User):
    name = "User"
    name_plural = "Users"
    icon = "fa-solid fa-users"
    category = "Users & Profiles"

    # List view – password intentionally excluded
    column_list = [
        User.id, User.username, User.email, User.user_type,
        User.phone, User.location, User.language, User.is_active, User.created_at,
    ]
    column_details_list = [
        User.id, User.username, User.email, User.user_type,
        User.phone, User.location, User.language, User.is_active,
        User.created_at, User.updated_at,
    ]
    # password included so admin can reset it; on_model_change hashes it
    form_columns = [
        User.username, User.email, User.password, User.user_type,
        User.phone, User.location, User.language, User.is_active,
    ]
    column_searchable_list = [User.username, User.email, User.phone]
    column_sortable_list = [User.id, User.username, User.email, User.user_type, User.created_at]
    column_filters = [
        StaticValuesFilter(User.user_type, values=[
            ("citizen", "Citizen"), ("lawyer", "Lawyer"),
            ("social_worker", "Social Worker"), ("admin", "Admin"),
        ]),
        BooleanFilter(User.is_active),
    ]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]

    async def on_model_change(self, data: dict, model: Any, is_created: bool, request: Request) -> None:
        """Hash password before saving; skip if field left blank on edit."""
        raw = data.get("password", "")
        if raw:
            data["password"] = get_password_hash(raw)
        elif not is_created:
            # Keep existing hash when password field is left empty
            data.pop("password", None)


class CitizenProfileAdmin(ModelView, model=CitizenProfile):
    name = "Citizen Profile"
    name_plural = "Citizen Profiles"
    icon = "fa-solid fa-id-card"
    category = "Users & Profiles"

    # user relationship included → sqladmin does a single selectinload
    column_list = [
        CitizenProfile.id, "user", CitizenProfile.full_name,
        CitizenProfile.city, CitizenProfile.state, CitizenProfile.gender,
        CitizenProfile.is_kyc_verified, CitizenProfile.created_at,
    ]
    column_details_list = [
        CitizenProfile.id, CitizenProfile.user_id, CitizenProfile.full_name,
        CitizenProfile.date_of_birth, CitizenProfile.gender,
        CitizenProfile.address, CitizenProfile.city, CitizenProfile.state,
        CitizenProfile.pincode, CitizenProfile.aadhar_number, CitizenProfile.pan_number,
        CitizenProfile.is_kyc_verified, CitizenProfile.kyc_verified_at,
        CitizenProfile.profile_picture_url, CitizenProfile.bio,
        CitizenProfile.created_at, CitizenProfile.updated_at,
    ]
    form_columns = [
        "user",                                  # Select2 — NOT NULL
        CitizenProfile.full_name, CitizenProfile.date_of_birth,
        CitizenProfile.gender, CitizenProfile.address, CitizenProfile.city,
        CitizenProfile.state, CitizenProfile.pincode,
        CitizenProfile.aadhar_number, CitizenProfile.pan_number,
        CitizenProfile.is_kyc_verified, CitizenProfile.kyc_verified_at,
        CitizenProfile.profile_picture_url, CitizenProfile.bio,
    ]
    column_searchable_list = [CitizenProfile.full_name, CitizenProfile.city, CitizenProfile.state]
    column_sortable_list = [CitizenProfile.id, CitizenProfile.full_name, CitizenProfile.is_kyc_verified]
    column_filters = [
        BooleanFilter(CitizenProfile.is_kyc_verified),
        AllUniqueStringValuesFilter(CitizenProfile.state),
        StaticValuesFilter(CitizenProfile.gender, values=[
            ("male", "Male"), ("female", "Female"), ("other", "Other"),
        ]),
    ]
    column_formatters = {
        "user": lambda m, a: _user_label(m.user),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class LawyerAdmin(ModelView, model=Lawyer):
    name = "Lawyer Profile"
    name_plural = "Lawyer Profiles"
    icon = "fa-solid fa-scale-balanced"
    category = "Users & Profiles"

    column_list = [
        Lawyer.id, "user", Lawyer.name, Lawyer.specialization,
        Lawyer.experience, Lawyer.rating, Lawyer.verified,
        Lawyer.total_cases, Lawyer.total_clients, Lawyer.created_at,
    ]
    column_details_list = [
        Lawyer.id, Lawyer.user_id, Lawyer.name, Lawyer.email, Lawyer.phone,
        Lawyer.specialization, Lawyer.experience, Lawyer.location, Lawyer.bio,
        Lawyer.rating, Lawyer.fee_range, Lawyer.verified, Lawyer.languages,
        Lawyer.total_cases, Lawyer.total_clients,
        Lawyer.created_at, Lawyer.updated_at,
    ]
    form_columns = [
        "user",                                  # Select2 — NOT NULL, unique
        Lawyer.name, Lawyer.email, Lawyer.phone,
        Lawyer.specialization, Lawyer.experience, Lawyer.location, Lawyer.bio,
        Lawyer.rating, Lawyer.fee_range, Lawyer.verified, Lawyer.languages,
        Lawyer.total_cases, Lawyer.total_clients,
    ]
    column_searchable_list = [Lawyer.name, Lawyer.email, Lawyer.specialization, Lawyer.location]
    column_sortable_list = [Lawyer.id, Lawyer.name, Lawyer.rating, Lawyer.experience, Lawyer.verified]
    column_filters = [
        BooleanFilter(Lawyer.verified),
        AllUniqueStringValuesFilter(Lawyer.specialization),
    ]
    column_formatters = {
        "user": lambda m, a: _user_label(m.user),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class AgencyAdmin(ModelView, model=Agency):
    name = "Agency"
    name_plural = "Agencies"
    icon = "fa-solid fa-building"
    category = "Users & Profiles"

    column_list = [
        Agency.id, Agency.name, Agency.phone, Agency.email,
        Agency.contact_person, Agency.is_verified, Agency.created_at,
    ]
    column_details_list = [
        Agency.id, Agency.name, Agency.description, Agency.address,
        Agency.phone, Agency.email, Agency.contact_person,
        Agency.is_verified, Agency.created_at, Agency.updated_at,
    ]
    form_columns = [
        Agency.name, Agency.description, Agency.address,
        Agency.phone, Agency.email, Agency.contact_person, Agency.is_verified,
    ]
    column_searchable_list = [Agency.name, Agency.email, Agency.contact_person]
    column_sortable_list = [Agency.id, Agency.name, Agency.is_verified]
    column_filters = [BooleanFilter(Agency.is_verified)]

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class SocialWorkerProfileAdmin(ModelView, model=SocialWorkerProfile):
    name = "Social Worker Profile"
    name_plural = "Social Worker Profiles"
    icon = "fa-solid fa-hand-holding-heart"
    category = "Users & Profiles"

    column_list = [
        SocialWorkerProfile.id, "user", "agency",
        SocialWorkerProfile.specialization, SocialWorkerProfile.is_verified,
        SocialWorkerProfile.total_referrals, SocialWorkerProfile.successful_referrals,
    ]
    column_details_list = [
        SocialWorkerProfile.id, SocialWorkerProfile.user_id, SocialWorkerProfile.agency_id,
        SocialWorkerProfile.license_number, SocialWorkerProfile.specialization,
        SocialWorkerProfile.bio, SocialWorkerProfile.is_verified, SocialWorkerProfile.verified_at,
        SocialWorkerProfile.total_referrals, SocialWorkerProfile.successful_referrals,
        SocialWorkerProfile.created_at, SocialWorkerProfile.updated_at,
    ]
    form_columns = [
        "user", "agency",                        # Select2 — both NOT NULL
        SocialWorkerProfile.license_number, SocialWorkerProfile.specialization,
        SocialWorkerProfile.bio, SocialWorkerProfile.is_verified, SocialWorkerProfile.verified_at,
        SocialWorkerProfile.total_referrals, SocialWorkerProfile.successful_referrals,
    ]
    column_searchable_list = [SocialWorkerProfile.specialization, SocialWorkerProfile.license_number]
    column_sortable_list = [SocialWorkerProfile.id, SocialWorkerProfile.is_verified, SocialWorkerProfile.total_referrals]
    column_filters = [BooleanFilter(SocialWorkerProfile.is_verified)]
    column_formatters = {
        "user": lambda m, a: _user_label(m.user),
        "agency": lambda m, a: m.agency.name if m.agency else "—",
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


# ══════════════════════════════════════════════
# LEGAL
# ══════════════════════════════════════════════

class CaseAdmin(ModelView, model=Case):
    name = "Case"
    name_plural = "Cases"
    icon = "fa-solid fa-gavel"
    category = "Legal"

    column_list = [
        Case.id, Case.case_number, Case.title, "user", "lawyer",
        Case.category, Case.status, Case.priority, Case.created_at,
    ]
    column_details_list = [
        Case.id, Case.case_number, Case.title, Case.description,
        Case.user_id, Case.lawyer_id, Case.category,
        Case.status, Case.priority, Case.created_at, Case.updated_at,
    ]
    form_columns = [
        "user", "lawyer",                        # Select2 dropdowns — prevents null on required FK
        Case.title, Case.description,
        Case.category, Case.status, Case.priority, Case.case_number,
    ]
    column_searchable_list = [Case.title, Case.case_number, Case.category]
    column_sortable_list = [Case.id, Case.case_number, Case.status, Case.priority, Case.created_at]
    column_filters = [
        StaticValuesFilter(Case.status, values=[
            ("open", "Open"), ("in_progress", "In Progress"),
            ("closed", "Closed"), ("resolved", "Resolved"),
        ]),
        StaticValuesFilter(Case.priority, values=[
            ("low", "Low"), ("medium", "Medium"), ("high", "High"),
        ]),
        AllUniqueStringValuesFilter(Case.category),
    ]
    column_formatters = {
        "user": lambda m, a: _user_label(m.user),
        "lawyer": lambda m, a: _user_label(m.lawyer),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class ConsultationAdmin(ModelView, model=Consultation):
    name = "Consultation"
    name_plural = "Consultations"
    icon = "fa-solid fa-calendar-check"
    category = "Legal"

    column_list = [
        Consultation.id, "user", "lawyer",
        Consultation.consultation_type, Consultation.status,
        Consultation.consultation_date, Consultation.duration_minutes,
        Consultation.fee_amount, Consultation.created_at,
    ]
    column_details_list = [
        Consultation.id, Consultation.user_id, Consultation.lawyer_id,
        Consultation.case_id, Consultation.consultation_type, Consultation.status,
        Consultation.scheduled_at, Consultation.consultation_date,
        Consultation.duration_minutes, Consultation.fee_amount,
        Consultation.notes, Consultation.created_at, Consultation.updated_at,
    ]
    form_columns = [
        "user", "lawyer", "case",                # Select2 — user/lawyer NOT NULL
        Consultation.consultation_type, Consultation.status,
        Consultation.scheduled_at, Consultation.consultation_date,
        Consultation.duration_minutes, Consultation.fee_amount, Consultation.notes,
    ]
    column_searchable_list = [Consultation.consultation_type]
    column_sortable_list = [Consultation.id, Consultation.status, Consultation.consultation_date, Consultation.fee_amount]
    column_filters = [
        StaticValuesFilter(Consultation.status, values=[
            ("scheduled", "Scheduled"), ("completed", "Completed"), ("cancelled", "Cancelled"),
        ]),
        AllUniqueStringValuesFilter(Consultation.consultation_type),
    ]
    column_formatters = {
        "user": lambda m, a: _user_label(m.user),
        "lawyer": lambda m, a: _user_label(m.lawyer),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class CaseNoteAdmin(ModelView, model=CaseNote):
    name = "Case Note"
    name_plural = "Case Notes"
    icon = "fa-solid fa-note-sticky"
    category = "Legal"

    column_list = [
        CaseNote.id, "case", "lawyer", CaseNote.note_type,
        CaseNote.title, CaseNote.priority, CaseNote.is_private,
        CaseNote.is_completed, CaseNote.due_date, CaseNote.created_at,
    ]
    column_details_list = [
        CaseNote.id, CaseNote.case_id, CaseNote.lawyer_id,
        CaseNote.note_type, CaseNote.title, CaseNote.content,
        CaseNote.is_private, CaseNote.priority, CaseNote.due_date,
        CaseNote.is_completed, CaseNote.completed_at,
        CaseNote.created_at, CaseNote.updated_at,
    ]
    form_columns = [
        "case", "lawyer",                        # Select2 — both NOT NULL
        CaseNote.note_type, CaseNote.title, CaseNote.content,
        CaseNote.is_private, CaseNote.priority, CaseNote.due_date,
        CaseNote.is_completed, CaseNote.completed_at,
    ]
    column_searchable_list = [CaseNote.title, CaseNote.note_type]
    column_sortable_list = [CaseNote.id, CaseNote.priority, CaseNote.is_completed, CaseNote.due_date]
    column_filters = [
        AllUniqueStringValuesFilter(CaseNote.note_type),
        BooleanFilter(CaseNote.is_private),
        BooleanFilter(CaseNote.is_completed),
        StaticValuesFilter(CaseNote.priority, values=[
            ("low", "Low"), ("medium", "Medium"), ("high", "High"),
        ]),
    ]
    column_formatters = {
        "case": lambda m, a: f"Case #{m.case_id}" if m.case_id else "—",
        "lawyer": lambda m, a: _user_label(m.lawyer),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class ReferralAdmin(ModelView, model=Referral):
    name = "Referral"
    name_plural = "Referrals"
    icon = "fa-solid fa-share-nodes"
    category = "Legal"

    column_list = [
        Referral.id, "social_worker", "lawyer", "citizen",
        Referral.case_category, Referral.status, Referral.outcome,
        Referral.referral_date,
    ]
    column_details_list = [
        Referral.id, Referral.social_worker_id, Referral.lawyer_id,
        Referral.citizen_id, Referral.case_id, Referral.referral_reason,
        Referral.status, Referral.case_category, Referral.outcome,
        Referral.outcome_notes, Referral.referral_date,
        Referral.accepted_date, Referral.completed_date,
        Referral.created_at, Referral.updated_at,
    ]
    form_columns = [
        "social_worker", "lawyer", "citizen",    # Select2 — all NOT NULL
        "case",                                  # nullable FK — still nicer as dropdown
        Referral.referral_reason, Referral.status,
        Referral.case_category, Referral.outcome, Referral.outcome_notes,
        Referral.referral_date, Referral.accepted_date, Referral.completed_date,
    ]
    column_searchable_list = [Referral.case_category, Referral.referral_reason]
    column_sortable_list = [Referral.id, Referral.status, Referral.referral_date]
    column_filters = [
        StaticValuesFilter(Referral.status, values=[
            ("pending", "Pending"), ("accepted", "Accepted"),
            ("in_progress", "In Progress"), ("completed", "Completed"), ("closed", "Closed"),
        ]),
        AllUniqueStringValuesFilter(Referral.outcome),
        AllUniqueStringValuesFilter(Referral.case_category),
    ]
    column_formatters = {
        "social_worker": lambda m, a: _user_label(m.social_worker),
        "lawyer": lambda m, a: _user_label(m.lawyer),
        "citizen": lambda m, a: _user_label(m.citizen),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


# ══════════════════════════════════════════════
# FINANCE
# ══════════════════════════════════════════════

class PaymentAdmin(ModelView, model=Payment):
    name = "Payment"
    name_plural = "Payments"
    icon = "fa-solid fa-credit-card"
    category = "Finance"

    column_list = [
        Payment.id, "citizen", "lawyer", Payment.amount,
        Payment.payment_method, Payment.status, Payment.transaction_id,
        Payment.paid_at, Payment.created_at,
    ]
    column_details_list = [
        Payment.id, Payment.citizen_id, Payment.lawyer_id,
        Payment.consultation_id, Payment.case_id, Payment.amount,
        Payment.payment_method, Payment.status, Payment.transaction_id,
        Payment.description, Payment.paid_at, Payment.confirmed_at,
        Payment.created_at, Payment.updated_at,
    ]
    form_columns = [
        "citizen", "lawyer",                     # Select2 — both NOT NULL
        "consultation", "case",                  # nullable FKs — dropdowns prevent bad integers
        Payment.amount, Payment.payment_method,
        Payment.status, Payment.transaction_id, Payment.description,
        Payment.paid_at, Payment.confirmed_at,
    ]
    column_searchable_list = [Payment.transaction_id, Payment.payment_method]
    column_sortable_list = [Payment.id, Payment.amount, Payment.status, Payment.paid_at, Payment.created_at]
    column_filters = [
        StaticValuesFilter(Payment.status, values=[
            ("pending", "Pending"), ("completed", "Completed"),
            ("failed", "Failed"), ("refunded", "Refunded"),
        ]),
        AllUniqueStringValuesFilter(Payment.payment_method),
    ]
    column_formatters = {
        "citizen": lambda m, a: _user_label(m.citizen),
        "lawyer": lambda m, a: _user_label(m.lawyer),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class InvoiceAdmin(ModelView, model=Invoice):
    name = "Invoice"
    name_plural = "Invoices"
    icon = "fa-solid fa-file-invoice-dollar"
    category = "Finance"

    column_list = [
        Invoice.id, Invoice.invoice_number, "lawyer", "citizen",
        Invoice.amount, Invoice.tax_amount, Invoice.total_amount,
        Invoice.status, Invoice.issued_at, Invoice.due_date,
    ]
    column_details_list = [
        Invoice.id, Invoice.lawyer_id, Invoice.citizen_id,
        Invoice.case_id, Invoice.consultation_id, Invoice.invoice_number,
        Invoice.amount, Invoice.tax_percentage, Invoice.tax_amount,
        Invoice.total_amount, Invoice.description, Invoice.status,
        Invoice.issued_at, Invoice.due_date, Invoice.paid_at,
        Invoice.notes, Invoice.created_at, Invoice.updated_at,
    ]
    form_columns = [
        "lawyer", "citizen",                     # Select2 — both NOT NULL
        "case", "consultation",                  # nullable FK dropdowns
        Invoice.invoice_number, Invoice.amount,
        Invoice.tax_percentage, Invoice.tax_amount, Invoice.total_amount,
        Invoice.description, Invoice.status, Invoice.issued_at,
        Invoice.due_date, Invoice.paid_at, Invoice.notes,
    ]
    column_searchable_list = [Invoice.invoice_number, Invoice.description]
    column_sortable_list = [Invoice.id, Invoice.invoice_number, Invoice.total_amount, Invoice.status, Invoice.due_date]
    column_filters = [
        StaticValuesFilter(Invoice.status, values=[
            ("draft", "Draft"), ("issued", "Issued"), ("paid", "Paid"),
            ("overdue", "Overdue"), ("cancelled", "Cancelled"),
        ]),
    ]
    column_formatters = {
        "lawyer": lambda m, a: _user_label(m.lawyer),
        "citizen": lambda m, a: _user_label(m.citizen),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


# ══════════════════════════════════════════════
# COMMUNICATION
# ══════════════════════════════════════════════

class DirectMessageAdmin(ModelView, model=DirectMessage):
    name = "Direct Message"
    name_plural = "Direct Messages"
    icon = "fa-solid fa-envelope"
    category = "Communication"

    column_list = [
        DirectMessage.id, "sender", "receiver",
        DirectMessage.message, DirectMessage.sent_at, DirectMessage.read_at,
    ]
    column_details_list = [
        DirectMessage.id, DirectMessage.sender_id, DirectMessage.receiver_id,
        DirectMessage.message, DirectMessage.sent_at, DirectMessage.read_at,
    ]
    form_columns = [
        "sender", "receiver",                    # Select2 — both NOT NULL
        DirectMessage.message, DirectMessage.read_at,
    ]
    column_searchable_list = [DirectMessage.message]
    column_sortable_list = [DirectMessage.id, DirectMessage.sent_at, DirectMessage.read_at]
    column_filters = []
    column_formatters = {
        "sender": lambda m, a: _user_label(m.sender),
        "receiver": lambda m, a: _user_label(m.receiver),
        "message": lambda m, a: (m.message[:60] + "…") if m.message and len(m.message) > 60 else m.message,
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class ChatMessageAdmin(ModelView, model=ChatMessage):
    name = "Chat Message"
    name_plural = "Chat Messages"
    icon = "fa-solid fa-robot"
    category = "Communication"

    column_list = [
        ChatMessage.id, "user", ChatMessage.language,
        ChatMessage.message, ChatMessage.created_at,
    ]
    column_details_list = [
        ChatMessage.id, ChatMessage.user_id, ChatMessage.message,
        ChatMessage.response, ChatMessage.language, ChatMessage.created_at,
    ]
    form_columns = [
        "user",                                  # Select2 — NOT NULL
        ChatMessage.message, ChatMessage.response, ChatMessage.language,
    ]
    column_searchable_list = [ChatMessage.message, ChatMessage.language]
    column_sortable_list = [ChatMessage.id, ChatMessage.language, ChatMessage.created_at]
    column_filters = [AllUniqueStringValuesFilter(ChatMessage.language)]
    column_formatters = {
        "user": lambda m, a: _user_label(m.user),
        "message": lambda m, a: (m.message[:60] + "…") if m.message and len(m.message) > 60 else m.message,
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class NotificationAdmin(ModelView, model=Notification):
    name = "Notification"
    name_plural = "Notifications"
    icon = "fa-solid fa-bell"
    category = "Communication"

    column_list = [
        Notification.id, "user", Notification.notification_type,
        Notification.title, Notification.is_read,
        Notification.read_at, Notification.created_at,
    ]
    column_details_list = [
        Notification.id, Notification.user_id, Notification.notification_type,
        Notification.title, Notification.message, Notification.related_id,
        Notification.is_read, Notification.read_at, Notification.created_at,
    ]
    form_columns = [
        "user",                                  # Select2 — NOT NULL
        Notification.notification_type, Notification.title, Notification.message,
        Notification.related_id, Notification.is_read, Notification.read_at,
    ]
    column_searchable_list = [Notification.title, Notification.notification_type]
    column_sortable_list = [Notification.id, Notification.notification_type, Notification.is_read, Notification.created_at]
    column_filters = [
        AllUniqueStringValuesFilter(Notification.notification_type),
        BooleanFilter(Notification.is_read),
    ]
    column_formatters = {
        "user": lambda m, a: _user_label(m.user),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


# ══════════════════════════════════════════════
# LAWYER MANAGEMENT
# ══════════════════════════════════════════════

class LawyerCredentialAdmin(ModelView, model=LawyerCredential):
    name = "Lawyer Credential"
    name_plural = "Lawyer Credentials"
    icon = "fa-solid fa-certificate"
    category = "Lawyer Management"

    column_list = [
        LawyerCredential.id, "lawyer", LawyerCredential.license_number,
        LawyerCredential.license_state, LawyerCredential.bar_association,
        LawyerCredential.bar_admission_year, LawyerCredential.is_verified,
        LawyerCredential.verified_at,
    ]
    column_details_list = [
        LawyerCredential.id, LawyerCredential.lawyer_id,
        LawyerCredential.license_number, LawyerCredential.license_state,
        LawyerCredential.bar_association, LawyerCredential.bar_admission_year,
        LawyerCredential.qualifications, LawyerCredential.court_admissions,
        LawyerCredential.is_verified, LawyerCredential.verified_at,
        LawyerCredential.verification_documents,
        LawyerCredential.created_at, LawyerCredential.updated_at,
    ]
    form_columns = [
        "lawyer",                                # Select2 — NOT NULL
        LawyerCredential.license_number, LawyerCredential.license_state,
        LawyerCredential.bar_association, LawyerCredential.bar_admission_year,
        LawyerCredential.qualifications, LawyerCredential.court_admissions,
        LawyerCredential.is_verified, LawyerCredential.verified_at,
        LawyerCredential.verification_documents,
    ]
    column_searchable_list = [LawyerCredential.license_number, LawyerCredential.bar_association]
    column_sortable_list = [LawyerCredential.id, LawyerCredential.is_verified, LawyerCredential.bar_admission_year]
    column_filters = [
        BooleanFilter(LawyerCredential.is_verified),
        AllUniqueStringValuesFilter(LawyerCredential.license_state),
    ]
    column_formatters = {
        "lawyer": lambda m, a: _user_label(m.lawyer),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class LawyerAvailabilityAdmin(ModelView, model=LawyerAvailability):
    name = "Lawyer Availability"
    name_plural = "Lawyer Availability"
    icon = "fa-solid fa-clock"
    category = "Lawyer Management"

    column_list = [
        LawyerAvailability.id, "lawyer", LawyerAvailability.day_of_week,
        LawyerAvailability.start_time, LawyerAvailability.end_time,
        LawyerAvailability.is_available, LawyerAvailability.slot_duration_minutes,
        LawyerAvailability.date_specific,
    ]
    column_details_list = [
        LawyerAvailability.id, LawyerAvailability.lawyer_id,
        LawyerAvailability.day_of_week, LawyerAvailability.start_time,
        LawyerAvailability.end_time, LawyerAvailability.is_available,
        LawyerAvailability.date_specific, LawyerAvailability.slot_duration_minutes,
        LawyerAvailability.break_start, LawyerAvailability.break_end,
        LawyerAvailability.created_at, LawyerAvailability.updated_at,
    ]
    form_columns = [
        "lawyer",                                # Select2 — NOT NULL
        LawyerAvailability.day_of_week, LawyerAvailability.start_time,
        LawyerAvailability.end_time, LawyerAvailability.is_available,
        LawyerAvailability.date_specific, LawyerAvailability.slot_duration_minutes,
        LawyerAvailability.break_start, LawyerAvailability.break_end,
    ]
    column_searchable_list = []
    column_sortable_list = [LawyerAvailability.id, LawyerAvailability.day_of_week, LawyerAvailability.is_available]
    column_filters = [
        BooleanFilter(LawyerAvailability.is_available),
        StaticValuesFilter(LawyerAvailability.day_of_week, values=[
            ("0", "Monday"), ("1", "Tuesday"), ("2", "Wednesday"),
            ("3", "Thursday"), ("4", "Friday"), ("5", "Saturday"), ("6", "Sunday"),
        ]),
    ]
    column_formatters = {
        "lawyer": lambda m, a: _user_label(m.lawyer),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class LawyerReviewAdmin(ModelView, model=LawyerReview):
    name = "Lawyer Review"
    name_plural = "Lawyer Reviews"
    icon = "fa-solid fa-star"
    category = "Lawyer Management"

    column_list = [
        LawyerReview.id, "lawyer", "citizen", LawyerReview.rating,
        LawyerReview.title, LawyerReview.communication_rating,
        LawyerReview.professionalism_rating, LawyerReview.effectiveness_rating,
        LawyerReview.is_verified_client, LawyerReview.created_at,
    ]
    column_details_list = [
        LawyerReview.id, LawyerReview.lawyer_id, LawyerReview.citizen_id,
        LawyerReview.case_id, LawyerReview.rating, LawyerReview.title,
        LawyerReview.review_text, LawyerReview.communication_rating,
        LawyerReview.professionalism_rating, LawyerReview.effectiveness_rating,
        LawyerReview.is_verified_client, LawyerReview.helpful_count,
        LawyerReview.unhelpful_count, LawyerReview.created_at, LawyerReview.updated_at,
    ]
    form_columns = [
        "lawyer", "citizen",                     # Select2 — both NOT NULL
        "case",                                  # nullable FK dropdown
        LawyerReview.rating, LawyerReview.title, LawyerReview.review_text,
        LawyerReview.communication_rating, LawyerReview.professionalism_rating,
        LawyerReview.effectiveness_rating, LawyerReview.is_verified_client,
        LawyerReview.helpful_count, LawyerReview.unhelpful_count,
    ]
    column_searchable_list = [LawyerReview.title, LawyerReview.review_text]
    column_sortable_list = [LawyerReview.id, LawyerReview.rating, LawyerReview.created_at]
    column_filters = [
        StaticValuesFilter(LawyerReview.rating, values=[
            ("1", "1 Star"), ("2", "2 Stars"), ("3", "3 Stars"),
            ("4", "4 Stars"), ("5", "5 Stars"),
        ]),
        BooleanFilter(LawyerReview.is_verified_client),
    ]
    column_formatters = {
        "lawyer": lambda m, a: _user_label(m.lawyer),
        "citizen": lambda m, a: _user_label(m.citizen),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


class DocumentTemplateAdmin(ModelView, model=DocumentTemplate):
    name = "Document Template"
    name_plural = "Document Templates"
    icon = "fa-solid fa-file-code"
    category = "Lawyer Management"

    column_list = [
        DocumentTemplate.id, "lawyer", DocumentTemplate.name,
        DocumentTemplate.template_type, DocumentTemplate.category,
        DocumentTemplate.is_public, DocumentTemplate.usage_count,
        DocumentTemplate.created_at,
    ]
    column_details_list = [
        DocumentTemplate.id, DocumentTemplate.lawyer_id, DocumentTemplate.name,
        DocumentTemplate.description, DocumentTemplate.template_type,
        DocumentTemplate.content, DocumentTemplate.is_public, DocumentTemplate.category,
        DocumentTemplate.tags, DocumentTemplate.usage_count,
        DocumentTemplate.created_at, DocumentTemplate.updated_at,
    ]
    form_columns = [
        "lawyer",                                # Select2 — NOT NULL
        DocumentTemplate.name, DocumentTemplate.description,
        DocumentTemplate.template_type, DocumentTemplate.content,
        DocumentTemplate.is_public, DocumentTemplate.category,
        DocumentTemplate.tags, DocumentTemplate.usage_count,
    ]
    column_searchable_list = [DocumentTemplate.name, DocumentTemplate.template_type, DocumentTemplate.tags]
    column_sortable_list = [DocumentTemplate.id, DocumentTemplate.name, DocumentTemplate.usage_count, DocumentTemplate.is_public]
    column_filters = [
        AllUniqueStringValuesFilter(DocumentTemplate.template_type),
        BooleanFilter(DocumentTemplate.is_public),
        AllUniqueStringValuesFilter(DocumentTemplate.category),
    ]
    column_formatters = {
        "lawyer": lambda m, a: _user_label(m.lawyer),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


# ══════════════════════════════════════════════
# DOCUMENTS
# ══════════════════════════════════════════════

class DocumentUploadAdmin(ModelView, model=DocumentUpload):
    name = "Document Upload"
    name_plural = "Document Uploads"
    icon = "fa-solid fa-file-arrow-up"
    category = "Documents"

    column_list = [
        DocumentUpload.id, "user", DocumentUpload.file_name,
        DocumentUpload.document_type, DocumentUpload.file_size,
        DocumentUpload.mime_type, DocumentUpload.is_verified,
        DocumentUpload.uploaded_at,
    ]
    column_details_list = [
        DocumentUpload.id, DocumentUpload.user_id, DocumentUpload.case_id,
        DocumentUpload.document_type, DocumentUpload.file_name,
        DocumentUpload.file_url, DocumentUpload.file_size, DocumentUpload.mime_type,
        DocumentUpload.description, DocumentUpload.uploaded_by,
        DocumentUpload.is_verified, DocumentUpload.uploaded_at, DocumentUpload.updated_at,
    ]
    form_columns = [
        "user", "uploader",                      # Select2 — both NOT NULL
        "case",                                  # nullable FK dropdown
        DocumentUpload.document_type, DocumentUpload.file_name,
        DocumentUpload.file_url, DocumentUpload.file_size,
        DocumentUpload.mime_type, DocumentUpload.description,
        DocumentUpload.is_verified,
    ]
    column_searchable_list = [DocumentUpload.file_name, DocumentUpload.document_type]
    column_sortable_list = [DocumentUpload.id, DocumentUpload.file_name, DocumentUpload.is_verified, DocumentUpload.uploaded_at]
    column_filters = [
        AllUniqueStringValuesFilter(DocumentUpload.document_type),
        BooleanFilter(DocumentUpload.is_verified),
        AllUniqueStringValuesFilter(DocumentUpload.mime_type),
    ]
    column_formatters = {
        "user": lambda m, a: _user_label(m.user),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


# ══════════════════════════════════════════════
# SECURITY
# ══════════════════════════════════════════════

class TwoFactorAuthAdmin(ModelView, model=TwoFactorAuth):
    name = "Two-Factor Auth"
    name_plural = "Two-Factor Auth"
    icon = "fa-solid fa-shield-halved"
    category = "Security"

    column_list = [
        TwoFactorAuth.id, "user", TwoFactorAuth.auth_method,
        TwoFactorAuth.is_enabled, TwoFactorAuth.phone_number,
        TwoFactorAuth.verified_at, TwoFactorAuth.created_at,
    ]
    # totp_secret and backup_codes visible only in the detail view (sensitive)
    column_details_list = [
        TwoFactorAuth.id, TwoFactorAuth.user_id, TwoFactorAuth.auth_method,
        TwoFactorAuth.is_enabled, TwoFactorAuth.phone_number,
        TwoFactorAuth.backup_codes, TwoFactorAuth.totp_secret,
        TwoFactorAuth.verified_at, TwoFactorAuth.created_at, TwoFactorAuth.updated_at,
    ]
    form_columns = [
        "user",                                  # Select2 — NOT NULL
        TwoFactorAuth.auth_method, TwoFactorAuth.is_enabled,
        TwoFactorAuth.phone_number, TwoFactorAuth.backup_codes,
        TwoFactorAuth.totp_secret, TwoFactorAuth.verified_at,
    ]
    column_searchable_list = [TwoFactorAuth.auth_method, TwoFactorAuth.phone_number]
    column_sortable_list = [TwoFactorAuth.id, TwoFactorAuth.is_enabled, TwoFactorAuth.auth_method]
    column_filters = [
        BooleanFilter(TwoFactorAuth.is_enabled),
        AllUniqueStringValuesFilter(TwoFactorAuth.auth_method),
    ]
    column_formatters = {
        "user": lambda m, a: _user_label(m.user),
    }

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    page_size = 25
    page_size_options = [10, 25, 50, 100]


# ──────────────────────────────────────────────
# Registry – imported by __init__.py
# ──────────────────────────────────────────────
all_views = [
    # Users & Profiles
    UserAdmin,
    CitizenProfileAdmin,
    LawyerAdmin,
    AgencyAdmin,
    SocialWorkerProfileAdmin,
    # Legal
    CaseAdmin,
    ConsultationAdmin,
    CaseNoteAdmin,
    ReferralAdmin,
    # Finance
    PaymentAdmin,
    InvoiceAdmin,
    # Communication
    DirectMessageAdmin,
    ChatMessageAdmin,
    NotificationAdmin,
    # Lawyer Management
    LawyerCredentialAdmin,
    LawyerAvailabilityAdmin,
    LawyerReviewAdmin,
    DocumentTemplateAdmin,
    # Documents
    DocumentUploadAdmin,
    # Security
    TwoFactorAuthAdmin,
]
