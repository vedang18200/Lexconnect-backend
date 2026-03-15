"""Fix permissions for all tables

Revision ID: fix_lawyer_reviews_permissions
Revises: social_worker_features_001
Create Date: 2026-03-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fix_lawyer_reviews_permissions'
down_revision: Union[str, Sequence[str], None] = 'social_worker_features_001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Grant permissions to legalaid_user on all tables."""

    # List of all tables in the database
    tables = [
        'users',
        'citizen_profiles',
        'lawyer_credentials',
        'lawyer_credential',
        'lawyers',
        'agencies',
        'social_worker_profiles',
        'cases',
        'case_notes',
        'case_note',
        'consultations',
        'lawyer_reviews',
        'payments',
        'chat_messages',
        'direct_messages',
        'notifications',
        'document_uploads',
        'document_templates',
        'document_template',
        'invoices',
        'invoice',
        'referrals',
        'lawyer_availability',
        'two_factor_auth',
    ]

    # Grant permissions on all tables
    for table in tables:
        try:
            op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO legalaid_user")
        except Exception:
            pass  # Ignore if table doesn't exist

    # Grant permissions on all sequences (for auto-increment columns)
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO legalaid_user")


def downgrade() -> None:
    """Revoke permissions from legalaid_user on all tables."""

    tables = [
        'users',
        'citizen_profiles',
        'lawyer_credentials',
        'lawyer_credential',
        'lawyers',
        'agencies',
        'social_worker_profiles',
        'cases',
        'case_notes',
        'case_note',
        'consultations',
        'lawyer_reviews',
        'payments',
        'chat_messages',
        'direct_messages',
        'notifications',
        'document_uploads',
        'document_templates',
        'document_template',
        'invoices',
        'invoice',
        'referrals',
        'lawyer_availability',
        'two_factor_auth',
    ]

    # Revoke permissions on all tables
    for table in tables:
        try:
            op.execute(f"REVOKE SELECT, INSERT, UPDATE, DELETE ON {table} FROM legalaid_user")
        except Exception:
            pass  # Ignore if table doesn't exist

    # Revoke permissions on all sequences
    op.execute("REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public FROM legalaid_user")
