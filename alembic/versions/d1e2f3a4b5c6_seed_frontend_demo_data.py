"""Seed frontend demo data

Revision ID: d1e2f3a4b5c6
Revises: c4d5e6f7a8b9
Create Date: 2026-04-08 00:30:00.000000

"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.database.models import (
    Case,
    ChatMessage,
    CitizenProfile,
    Consultation,
    DirectMessage,
    DocumentUpload,
    Lawyer,
    NotificationPreference,
    Payment,
    User,
)

# revision identifiers, used by Alembic.
revision: str = "d1e2f3a4b5c6"
down_revision: Union[str, Sequence[str], None] = "c4d5e6f7a8b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _sync_sequences(db: Session) -> None:
    tables = [
        "users",
        "lawyers",
        "citizen_profiles",
        "notification_preferences",
        "cases",
        "consultations",
        "direct_messages",
        "document_uploads",
        "payments",
        "chat_messages",
    ]
    for table_name in tables:
        db.execute(
            text(
                f"""
                SELECT setval(
                    pg_get_serial_sequence('{table_name}', 'id'),
                    COALESCE((SELECT MAX(id) FROM {table_name}), 0) + 1,
                    false
                )
                """
            )
        )


def _get_or_create_user(db: Session, username: str, email: str, user_type: str, phone: str, location: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if user:
        return user

    user = User(
        username=username,
        email=email,
        password=get_password_hash("demo12345"),
        user_type=user_type,
        phone=phone,
        location=location,
        language="en",
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def _ensure_lawyer_profile(db: Session, user: User, name: str, specialization: str, rating: float, experience: int) -> None:
    profile = db.query(Lawyer).filter(Lawyer.user_id == user.id).first()
    if profile:
        return

    db.add(
        Lawyer(
            user_id=user.id,
            name=name,
            email=user.email,
            phone=user.phone,
            specialization=specialization,
            location=user.location,
            experience=experience,
            rating=rating,
            verified=True,
        )
    )


def _ensure_citizen_profile(db: Session, user: User) -> CitizenProfile:
    profile = db.query(CitizenProfile).filter(CitizenProfile.user_id == user.id).first()
    if profile:
        return profile

    profile = CitizenProfile(
        user_id=user.id,
        full_name="Priya Sharma",
        gender="Female",
        occupation="Software Engineer",
        city="Bengaluru",
        state="Karnataka",
        pincode="560001",
        address="MG Road, Bengaluru",
        bio="Working professional seeking legal support for active cases.",
        aadhar_number="123456789012",
        is_kyc_verified=True,
        kyc_verified_at=datetime.now(timezone.utc) - timedelta(days=300),
    )
    db.add(profile)
    db.flush()
    return profile


def _ensure_notification_preferences(db: Session, user: User) -> None:
    prefs = db.query(NotificationPreference).filter(NotificationPreference.user_id == user.id).first()
    if prefs:
        return

    db.add(
        NotificationPreference(
            user_id=user.id,
            email_notifications=True,
            sms_notifications=True,
            case_updates=True,
            consultation_reminders=True,
            payment_alerts=True,
            marketing_emails=False,
        )
    )


def _ensure_cases(db: Session, citizen: User, lawyers: list[User]) -> list[Case]:
    titles = [
        "Cyber Crime Investigation",
        "Consumer Product Defect Claim",
        "Property Dispute Resolution",
        "Wrongful Termination",
    ]
    categories = ["Criminal", "Consumer", "Property", "Labour"]

    seeded: list[Case] = []
    for idx, title in enumerate(titles):
        existing = db.query(Case).filter(Case.user_id == citizen.id, Case.title == title).first()
        if existing:
            seeded.append(existing)
            continue

        case = Case(
            user_id=citizen.id,
            lawyer_id=lawyers[idx % len(lawyers)].id,
            title=title,
            category=categories[idx],
            description=f"Demo case for {title}",
            status="in_progress" if idx < 3 else "open",
            priority="high" if idx == 0 else "medium",
            case_number=f"DEMO-2026-{1000 + idx}",
            court_name="City Civil Court",
            hearing_date=datetime.now(timezone.utc) + timedelta(days=7 + idx),
            estimated_completion_date=datetime.now(timezone.utc) + timedelta(days=45 + idx * 10),
            case_progress=35 + idx * 10,
        )
        db.add(case)
        db.flush()
        seeded.append(case)
    return seeded


def _ensure_consultations(db: Session, citizen: User, lawyers: list[User], cases: list[Case]) -> None:
    now = datetime.now(timezone.utc)
    templates = [
        ("video", "scheduled", now + timedelta(days=2, hours=2), 45, 2500, "Bring all digital evidence and timeline."),
        ("phone", "scheduled", now + timedelta(days=4), 30, 1500, "Prepare issue summary points before call."),
        ("in-person", "completed", now - timedelta(days=3), 60, 3000, "Discussed hearing strategy and witness prep."),
        ("video", "cancelled", now - timedelta(days=1), 45, 2000, "Cancelled by lawyer due to emergency."),
        ("video", "completed", now - timedelta(days=9), 50, 2800, "Reviewed documents and drafted legal notice."),
    ]

    for idx, (mode, status, dt, duration, fee, notes) in enumerate(templates):
        case = cases[idx % len(cases)]
        lawyer = lawyers[idx % len(lawyers)]
        exists = db.query(Consultation).filter(
            Consultation.user_id == citizen.id,
            Consultation.lawyer_id == lawyer.id,
            Consultation.case_id == case.id,
            Consultation.consultation_date == dt,
        ).first()
        if exists:
            continue

        db.add(
            Consultation(
                user_id=citizen.id,
                lawyer_id=lawyer.id,
                case_id=case.id,
                consultation_type=mode,
                status=status,
                consultation_date=dt,
                scheduled_at=dt,
                duration_minutes=duration,
                fee_amount=fee,
                notes=notes,
            )
        )


def _ensure_messages(db: Session, citizen: User, lawyers: list[User], cases: list[Case]) -> None:
    now = datetime.now(timezone.utc)
    for idx, lawyer in enumerate(lawyers):
        existing = db.query(DirectMessage).filter(
            DirectMessage.sender_id == citizen.id,
            DirectMessage.receiver_id == lawyer.id,
        ).first()
        if existing:
            continue

        case = cases[idx % len(cases)]
        outgoing_1 = DirectMessage(
            sender_id=citizen.id,
            receiver_id=lawyer.id,
            message=f"Good morning! I wanted to discuss updates for {case.title}.",
            sent_at=now - timedelta(hours=5 - idx),
            read_at=now - timedelta(hours=4 - idx),
        )
        incoming_1 = DirectMessage(
            sender_id=lawyer.id,
            receiver_id=citizen.id,
            message="Yes, I reviewed the latest documents. We have a strong direction.",
            sent_at=now - timedelta(hours=4 - idx),
            read_at=now - timedelta(hours=3 - idx),
        )
        outgoing_2 = DirectMessage(
            sender_id=citizen.id,
            receiver_id=lawyer.id,
            message="Perfect. Should we schedule a prep call this week?",
            sent_at=now - timedelta(hours=2 - idx),
            read_at=None,
        )
        db.add_all([outgoing_1, incoming_1, outgoing_2])


def _ensure_documents(db: Session, citizen: User, cases: list[Case]) -> None:
    docs = [
        ("Aadhar Card.pdf", "Identity Proof", True),
        ("PAN Card.pdf", "Identity Proof", True),
        ("Address Proof.pdf", "Address Proof", True),
        ("Bank Statement.pdf", "Financial Document", False),
    ]

    for idx, (name, doc_type, verified) in enumerate(docs):
        exists = db.query(DocumentUpload).filter(
            DocumentUpload.user_id == citizen.id,
            DocumentUpload.file_name == name,
        ).first()
        if exists:
            continue

        db.add(
            DocumentUpload(
                user_id=citizen.id,
                case_id=cases[idx % len(cases)].id,
                document_type=doc_type,
                file_name=name,
                file_url=f"/files/{name}",
                file_size=800000 + idx * 30000,
                mime_type="application/pdf",
                description=f"Demo {doc_type}",
                uploaded_by=citizen.id,
                is_verified=verified,
                uploaded_at=datetime.now(timezone.utc) - timedelta(days=20 - idx),
            )
        )


def _ensure_payments(db: Session, citizen: User, lawyers: list[User], cases: list[Case]) -> None:
    rows = [
        (2000, "credit_card", "completed", "Consultation Fee - Adv. Rajesh Kumar", 7),
        (3500, "upi", "completed", "Case Filing Support", 12),
        (1800, "net_banking", "pending", "Document Review Session", 3),
        (2500, "credit_card", "refunded", "Cancelled Consultation", 16),
        (2200, "upi", "failed", "Payment Retry Required", 1),
    ]

    for idx, (amount, method, status_value, desc, days_ago) in enumerate(rows):
        txid = f"TXN-DEMO-2026-{500 + idx}"
        exists = db.query(Payment).filter(Payment.transaction_id == txid).first()
        if exists:
            continue

        paid_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
        db.add(
            Payment(
                citizen_id=citizen.id,
                lawyer_id=lawyers[idx % len(lawyers)].id,
                case_id=cases[idx % len(cases)].id,
                amount=amount,
                payment_method=method,
                status=status_value,
                transaction_id=txid,
                description=desc,
                paid_at=paid_at if status_value == "completed" else None,
                confirmed_at=paid_at if status_value == "completed" else None,
                created_at=paid_at,
            )
        )


def _ensure_chat_history(db: Session, citizen: User) -> None:
    prompts = [
        (
            "What is a consumer complaint?",
            "A consumer complaint is a legal grievance for defective goods or deficient services.",
        ),
        (
            "How to file a property dispute?",
            "Collect title records and issue legal notice before starting civil proceedings.",
        ),
        (
            "Explain criminal law basics",
            "Criminal law governs offenses against the state and starts with complaint or FIR.",
        ),
        (
            "What are my rights as an employee?",
            "You have rights related to wages, workplace safety, and unfair termination protection.",
        ),
    ]

    for idx, (msg, response) in enumerate(prompts):
        exists = db.query(ChatMessage).filter(ChatMessage.user_id == citizen.id, ChatMessage.message == msg).first()
        if exists:
            continue

        db.add(
            ChatMessage(
                user_id=citizen.id,
                message=msg,
                response=response,
                language="en",
                created_at=datetime.now(timezone.utc) - timedelta(minutes=45 - idx * 7),
            )
        )


def upgrade() -> None:
    """Seed idempotent demo data for frontend previews."""
    db = Session(bind=op.get_bind())
    try:
        _sync_sequences(db)

        citizen = _get_or_create_user(
            db,
            username="demo_citizen",
            email="demo.citizen@lexconnect.test",
            user_type="citizen",
            phone="+91 9876543210",
            location="Bengaluru",
        )

        lawyer_1 = _get_or_create_user(
            db,
            username="adv_rajesh_kumar",
            email="rajesh.kumar@lexconnect.test",
            user_type="lawyer",
            phone="+91 9000000001",
            location="Bengaluru",
        )
        lawyer_2 = _get_or_create_user(
            db,
            username="adv_priya_mehta",
            email="priya.mehta@lexconnect.test",
            user_type="lawyer",
            phone="+91 9000000002",
            location="Mumbai",
        )
        lawyer_3 = _get_or_create_user(
            db,
            username="adv_lakshmi_iyer",
            email="lakshmi.iyer@lexconnect.test",
            user_type="lawyer",
            phone="+91 9000000003",
            location="Chennai",
        )

        lawyers = [lawyer_1, lawyer_2, lawyer_3]

        _ensure_lawyer_profile(db, lawyer_1, "Adv. Rajesh Kumar", "Criminal Law", 4.8, 12)
        _ensure_lawyer_profile(db, lawyer_2, "Adv. Priya Mehta", "Consumer Rights", 4.7, 10)
        _ensure_lawyer_profile(db, lawyer_3, "Adv. Lakshmi Iyer", "Property Law", 4.6, 9)

        _ensure_citizen_profile(db, citizen)
        _ensure_notification_preferences(db, citizen)

        cases = _ensure_cases(db, citizen, lawyers)
        _ensure_consultations(db, citizen, lawyers, cases)
        _ensure_messages(db, citizen, lawyers, cases)
        _ensure_documents(db, citizen, cases)
        _ensure_payments(db, citizen, lawyers, cases)
        _ensure_chat_history(db, citizen)

        db.commit()
    finally:
        db.close()


def downgrade() -> None:
    """Remove seeded demo data."""
    db = Session(bind=op.get_bind())
    try:
        demo_usernames = [
            "demo_citizen",
            "adv_rajesh_kumar",
            "adv_priya_mehta",
            "adv_lakshmi_iyer",
        ]
        users = db.query(User).filter(User.username.in_(demo_usernames)).all()
        user_ids = [u.id for u in users]

        if user_ids:
            db.query(ChatMessage).filter(ChatMessage.user_id.in_(user_ids)).delete(synchronize_session=False)
            db.query(DirectMessage).filter(
                (DirectMessage.sender_id.in_(user_ids)) | (DirectMessage.receiver_id.in_(user_ids))
            ).delete(synchronize_session=False)
            db.query(Consultation).filter(
                (Consultation.user_id.in_(user_ids)) | (Consultation.lawyer_id.in_(user_ids))
            ).delete(synchronize_session=False)
            db.query(Payment).filter(
                (Payment.citizen_id.in_(user_ids)) | (Payment.lawyer_id.in_(user_ids))
            ).delete(synchronize_session=False)
            db.query(DocumentUpload).filter(DocumentUpload.user_id.in_(user_ids)).delete(synchronize_session=False)
            db.query(Case).filter(Case.user_id.in_(user_ids)).delete(synchronize_session=False)
            db.query(NotificationPreference).filter(NotificationPreference.user_id.in_(user_ids)).delete(synchronize_session=False)
            db.query(CitizenProfile).filter(CitizenProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
            db.query(Lawyer).filter(Lawyer.user_id.in_(user_ids)).delete(synchronize_session=False)
            db.query(User).filter(User.id.in_(user_ids)).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()
