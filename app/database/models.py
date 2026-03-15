"""SQLAlchemy database models"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.db import Base
from datetime import datetime, timezone

class User(Base):
    """User model"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    location = Column(String(255), nullable=True)
    language = Column(String(50), nullable=True)
    user_type = Column(String(50), nullable=False)  # citizen, lawyer, social_worker, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lawyer_profile = relationship("Lawyer", back_populates="user", uselist=False)
    citizen_profile = relationship("CitizenProfile", back_populates="user", uselist=False)
    social_worker_profile = relationship(
        "SocialWorkerProfile",
        uselist=False,
        foreign_keys="SocialWorkerProfile.user_id",
        back_populates="user",
    )
    cases = relationship("Case", back_populates="user", foreign_keys="Case.user_id")
    lawyer_cases = relationship("Case", back_populates="lawyer", foreign_keys="Case.lawyer_id")
    consultations = relationship("Consultation", back_populates="user", foreign_keys="Consultation.user_id")
    lawyer_consultations = relationship("Consultation", back_populates="lawyer", foreign_keys="Consultation.lawyer_id")
    sent_messages = relationship("DirectMessage", back_populates="sender", foreign_keys="DirectMessage.sender_id")
    received_messages = relationship("DirectMessage", back_populates="receiver", foreign_keys="DirectMessage.receiver_id")
    chat_messages = relationship("ChatMessage", back_populates="user")
    two_factor_auth = relationship("TwoFactorAuth", back_populates="user", uselist=False)

    __table_args__ = (
        Index('ix_users_id', 'id'),
    )


class Lawyer(Base):
    """Lawyer profile model"""
    __tablename__ = "lawyers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    specialization = Column(String(255), nullable=True)
    experience = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    rating = Column(Numeric(3, 2), nullable=True)
    fee_range = Column(String(100), nullable=True)
    verified = Column(Boolean, default=False)
    languages = Column(String(500), nullable=True)
    total_cases = Column(Integer, default=0)
    total_clients = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="lawyer_profile")

    __table_args__ = (
        Index('ix_lawyers_id', 'id'),
    )


class Case(Base):
    """Legal case model"""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=True)
    status = Column(String(100), default="open")  # open, in_progress, closed, resolved
    priority = Column(String(50), default="medium")  # low, medium, high
    case_number = Column(String(100), unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="cases", foreign_keys=[user_id])
    lawyer = relationship("User", back_populates="lawyer_cases", foreign_keys=[lawyer_id])

    __table_args__ = (
        Index('ix_cases_id', 'id'),
    )


class Consultation(Base):
    """Consultation model"""
    __tablename__ = "consultations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    consultation_type = Column(String(100), nullable=True)
    status = Column(String(100), default="scheduled")  # scheduled, completed, cancelled
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    consultation_date = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    fee_amount = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="consultations", foreign_keys=[user_id])
    lawyer = relationship("User", back_populates="lawyer_consultations", foreign_keys=[lawyer_id])

    __table_args__ = (
        Index('ix_consultations_id', 'id'),
    )


class DirectMessage(Base):
    """Direct message model"""
    __tablename__ = "direct_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    sender = relationship("User", back_populates="sent_messages", foreign_keys=[sender_id])
    receiver = relationship("User", back_populates="received_messages", foreign_keys=[receiver_id])

    __table_args__ = (
        Index('ix_direct_messages_id', 'id'),
    )


class ChatMessage(Base):
    """AI Chatbot message model"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    response = Column(Text, nullable=True)
    language = Column(String(50), default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="chat_messages")

    __table_args__ = (
        Index('ix_chat_messages_id', 'id'),
    )


class CitizenProfile(Base):
    """Citizen profile extended information"""
    __tablename__ = "citizen_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    gender = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(6), nullable=True)
    aadhar_number = Column(String(255), nullable=True)  # Encrypted
    pan_number = Column(String(255), nullable=True)     # Encrypted
    is_kyc_verified = Column(Boolean, default=False)
    kyc_verified_at = Column(DateTime(timezone=True), nullable=True)
    profile_picture_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="citizen_profile")

    __table_args__ = (
        Index('ix_citizen_profiles_user_id', 'user_id'),
    )


class DocumentUpload(Base):
    """Uploaded documents for cases"""
    __tablename__ = "document_uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    document_type = Column(String(100), nullable=True)  # contract, license, statement, etc.
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_verified = Column(Boolean, default=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    case = relationship("Case")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    __table_args__ = (
        Index('ix_document_uploads_user_id', 'user_id'),
        Index('ix_document_uploads_case_id', 'case_id'),
    )


class LawyerReview(Base):
    """Reviews and ratings for lawyers"""
    __tablename__ = "lawyer_reviews"

    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(255), nullable=True)
    review_text = Column(Text, nullable=True)
    communication_rating = Column(Integer, nullable=True)  # 1-5
    professionalism_rating = Column(Integer, nullable=True)  # 1-5
    effectiveness_rating = Column(Integer, nullable=True)  # 1-5
    is_verified_client = Column(Boolean, default=True)
    helpful_count = Column(Integer, default=0)
    unhelpful_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lawyer = relationship("User", foreign_keys=[lawyer_id])
    citizen = relationship("User", foreign_keys=[citizen_id])
    case = relationship("Case")

    __table_args__ = (
        Index('ix_lawyer_reviews_lawyer_id', 'lawyer_id'),
        Index('ix_lawyer_reviews_citizen_id', 'citizen_id'),
    )


class Payment(Base):
    """Payment transactions"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    payment_method = Column(String(50), nullable=False)  # credit_card, debit_card, upi, etc.
    status = Column(String(50), default="pending")  # pending, completed, failed, refunded
    transaction_id = Column(String(255), unique=True, nullable=True)
    description = Column(String(500), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    citizen = relationship("User", foreign_keys=[citizen_id])
    lawyer = relationship("User", foreign_keys=[lawyer_id])
    consultation = relationship("Consultation")
    case = relationship("Case")

    __table_args__ = (
        Index('ix_payments_citizen_id', 'citizen_id'),
        Index('ix_payments_lawyer_id', 'lawyer_id'),
        Index('ix_payments_status', 'status'),
    )


class TwoFactorAuth(Base):
    """Two-factor authentication settings"""
    __tablename__ = "two_factor_auth"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    is_enabled = Column(Boolean, default=False)
    auth_method = Column(String(50), nullable=True)  # sms, email, totp, etc.
    phone_number = Column(String(20), nullable=True)
    backup_codes = Column(Text, nullable=True)  # Encrypted JSON array
    totp_secret = Column(String(255), nullable=True)  # Encrypted
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="two_factor_auth")

    __table_args__ = (
        Index('ix_two_factor_auth_user_id', 'user_id'),
    )


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type = Column(String(50), nullable=False)  # consultation_scheduled, case_updated, payment_received, etc.
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    related_id = Column(Integer, nullable=True)  # ID of the related entity (case, consultation, etc.)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('ix_notifications_user_id', 'user_id'),
        Index('ix_notifications_created_at', 'created_at'),
    )


class LawyerCredential(Base):
    """Lawyer professional credentials and verification"""
    __tablename__ = "lawyer_credentials"

    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    license_number = Column(String(255), nullable=False)
    license_state = Column(String(100), nullable=True)
    bar_association = Column(String(255), nullable=True)
    bar_admission_year = Column(Integer, nullable=True)
    qualifications = Column(Text, nullable=True)  # JSON array of degrees/certifications
    court_admissions = Column(Text, nullable=True)  # JSON array of courts
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verification_documents = Column(Text, nullable=True)  # JSON with document URLs
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lawyer = relationship("User", foreign_keys=[lawyer_id])

    __table_args__ = (
        Index('ix_lawyer_credentials_lawyer_id', 'lawyer_id'),
    )


class LawyerAvailability(Base):
    """Lawyer consultation availability slots"""
    __tablename__ = "lawyer_availability"

    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    day_of_week = Column(Integer, nullable=True)  # 0-6 (Monday-Sunday)
    start_time = Column(String(5), nullable=True)  # HH:MM format
    end_time = Column(String(5), nullable=True)  # HH:MM format
    is_available = Column(Boolean, default=True)
    date_specific = Column(DateTime(timezone=True), nullable=True)  # For specific date overrides
    slot_duration_minutes = Column(Integer, default=60)
    break_start = Column(String(5), nullable=True)
    break_end = Column(String(5), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lawyer = relationship("User", foreign_keys=[lawyer_id])

    __table_args__ = (
        Index('ix_lawyer_availability_lawyer_id', 'lawyer_id'),
    )


class Invoice(Base):
    """Invoices for payments"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    consultation_id = Column(Integer, ForeignKey("consultations.id"), nullable=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    tax_percentage = Column(Numeric(5, 2), nullable=True)
    tax_amount = Column(Numeric(10, 2), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="draft")  # draft, issued, paid, overdue, cancelled
    issued_at = Column(DateTime(timezone=True), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lawyer = relationship("User", foreign_keys=[lawyer_id])
    citizen = relationship("User", foreign_keys=[citizen_id])
    case = relationship("Case")
    consultation = relationship("Consultation")

    __table_args__ = (
        Index('ix_invoices_lawyer_id', 'lawyer_id'),
        Index('ix_invoices_citizen_id', 'citizen_id'),
        Index('ix_invoices_status', 'status'),
    )


class DocumentTemplate(Base):
    """Document templates for lawyers"""
    __tablename__ = "document_templates"

    id = Column(Integer, primary_key=True, index=True)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    template_type = Column(String(100), nullable=False)  # contract, agreement, petition, etc.
    content = Column(Text, nullable=False)  # Template content with placeholders
    is_public = Column(Boolean, default=False)  # Can be used by other lawyers
    category = Column(String(100), nullable=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    lawyer = relationship("User", foreign_keys=[lawyer_id])

    __table_args__ = (
        Index('ix_document_templates_lawyer_id', 'lawyer_id'),
        Index('ix_document_templates_template_type', 'template_type'),
    )


class CaseNote(Base):
    """Internal case notes and progress tracking"""
    __tablename__ = "case_notes"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    note_type = Column(String(50), nullable=True)  # progress, action_item, deadline, etc.
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    is_private = Column(Boolean, default=False)  # Only visible to lawyer
    priority = Column(String(50), nullable=True)  # low, medium, high
    due_date = Column(DateTime(timezone=True), nullable=True)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    case = relationship("Case")
    lawyer = relationship("User", foreign_keys=[lawyer_id])

    __table_args__ = (
        Index('ix_case_notes_case_id', 'case_id'),
        Index('ix_case_notes_lawyer_id', 'lawyer_id'),
        Index('ix_case_notes_is_completed', 'is_completed'),
    )


class Agency(Base):
    """Organization/Agency for social workers"""
    __tablename__ = "agencies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    contact_person = Column(String(255), nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    social_workers = relationship("SocialWorkerProfile", back_populates="agency")

    __table_args__ = (
        Index('ix_agencies_id', 'id'),
    )


class SocialWorkerProfile(Base):
    """Social worker profile and information"""
    __tablename__ = "social_worker_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    agency_id = Column(Integer, ForeignKey("agencies.id"), nullable=False)
    license_number = Column(String(255), nullable=True)
    specialization = Column(String(255), nullable=True)  # Counseling, case management, etc.
    bio = Column(Text, nullable=True)
    is_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    total_referrals = Column(Integer, default=0)
    successful_referrals = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="social_worker_profile")
    agency = relationship("Agency", back_populates="social_workers")
    # Referral.social_worker_id references users.id, so join via profile.user_id.
    referrals = relationship(
        "Referral",
        primaryjoin="SocialWorkerProfile.user_id == Referral.social_worker_id",
        foreign_keys="Referral.social_worker_id",
        viewonly=True,
    )

    __table_args__ = (
        Index('ix_social_worker_profiles_user_id', 'user_id'),
        Index('ix_social_worker_profiles_agency_id', 'agency_id'),
    )


class Referral(Base):
    """Referral of client to lawyer by social worker"""
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    social_worker_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    citizen_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=True)
    referral_reason = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, accepted, in_progress, completed, closed
    case_category = Column(String(255), nullable=True)
    outcome = Column(String(50), nullable=True)  # resolved, ongoing, unsuccessful, etc.
    outcome_notes = Column(Text, nullable=True)
    referral_date = Column(DateTime(timezone=True), server_default=func.now())
    accepted_date = Column(DateTime(timezone=True), nullable=True)
    completed_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    social_worker = relationship("User", foreign_keys=[social_worker_id])
    lawyer = relationship("User", foreign_keys=[lawyer_id])
    citizen = relationship("User", foreign_keys=[citizen_id])
    case = relationship("Case")

    __table_args__ = (
        Index('ix_referrals_social_worker_id', 'social_worker_id'),
        Index('ix_referrals_lawyer_id', 'lawyer_id'),
        Index('ix_referrals_citizen_id', 'citizen_id'),
        Index('ix_referrals_status', 'status'),
        Index('ix_referrals_created_at', 'created_at'),
    )
