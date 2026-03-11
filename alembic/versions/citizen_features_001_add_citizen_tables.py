"""Add citizen features tables

Revision ID: citizen_features_001
Revises: 77e379b5c9f0
Create Date: 2026-03-11 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'citizen_features_001'
down_revision: Union[str, Sequence[str], None] = '77e379b5c9f0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema with citizen feature tables."""

    # Create citizen_profiles table
    op.create_table('citizen_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('date_of_birth', sa.DateTime(timezone=True), nullable=True),
        sa.Column('gender', sa.String(length=20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('state', sa.String(length=100), nullable=True),
        sa.Column('pincode', sa.String(length=6), nullable=True),
        sa.Column('aadhar_number', sa.String(length=255), nullable=True),
        sa.Column('pan_number', sa.String(length=255), nullable=True),
        sa.Column('is_kyc_verified', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('kyc_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('profile_picture_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_citizen_profiles_user_id'), 'citizen_profiles', ['user_id'], unique=False)

    # Create document_uploads table
    op.create_table('document_uploads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=True),
        sa.Column('document_type', sa.String(length=100), nullable=True),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('file_url', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_uploads_case_id'), 'document_uploads', ['case_id'], unique=False)
    op.create_index(op.f('ix_document_uploads_user_id'), 'document_uploads', ['user_id'], unique=False)

    # Create lawyer_reviews table
    op.create_table('lawyer_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('citizen_id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('review_text', sa.Text(), nullable=True),
        sa.Column('communication_rating', sa.Integer(), nullable=True),
        sa.Column('professionalism_rating', sa.Integer(), nullable=True),
        sa.Column('effectiveness_rating', sa.Integer(), nullable=True),
        sa.Column('is_verified_client', sa.Boolean(), nullable=True, server_default='1'),
        sa.Column('helpful_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('unhelpful_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['citizen_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['lawyer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lawyer_reviews_citizen_id'), 'lawyer_reviews', ['citizen_id'], unique=False)
    op.create_index(op.f('ix_lawyer_reviews_lawyer_id'), 'lawyer_reviews', ['lawyer_id'], unique=False)

    # Create payments table
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('citizen_id', sa.Integer(), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('consultation_id', sa.Integer(), nullable=True),
        sa.Column('case_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_method', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, server_default='pending'),
        sa.Column('transaction_id', sa.String(length=255), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['citizen_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ),
        sa.ForeignKeyConstraint(['lawyer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('transaction_id')
    )
    op.create_index(op.f('ix_payments_citizen_id'), 'payments', ['citizen_id'], unique=False)
    op.create_index(op.f('ix_payments_lawyer_id'), 'payments', ['lawyer_id'], unique=False)
    op.create_index(op.f('ix_payments_status'), 'payments', ['status'], unique=False)

    # Create two_factor_auth table
    op.create_table('two_factor_auth',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('auth_method', sa.String(length=50), nullable=True),
        sa.Column('phone_number', sa.String(length=20), nullable=True),
        sa.Column('backup_codes', sa.Text(), nullable=True),
        sa.Column('totp_secret', sa.String(length=255), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_two_factor_auth_user_id'), 'two_factor_auth', ['user_id'], unique=False)

    # Create notifications table
    op.create_table('notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_created_at'), 'notifications', ['created_at'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema by dropping citizen feature tables."""
    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_created_at'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_two_factor_auth_user_id'), table_name='two_factor_auth')
    op.drop_table('two_factor_auth')

    op.drop_index(op.f('ix_payments_status'), table_name='payments')
    op.drop_index(op.f('ix_payments_lawyer_id'), table_name='payments')
    op.drop_index(op.f('ix_payments_citizen_id'), table_name='payments')
    op.drop_table('payments')

    op.drop_index(op.f('ix_lawyer_reviews_lawyer_id'), table_name='lawyer_reviews')
    op.drop_index(op.f('ix_lawyer_reviews_citizen_id'), table_name='lawyer_reviews')
    op.drop_table('lawyer_reviews')

    op.drop_index(op.f('ix_document_uploads_user_id'), table_name='document_uploads')
    op.drop_index(op.f('ix_document_uploads_case_id'), table_name='document_uploads')
    op.drop_table('document_uploads')

    op.drop_index(op.f('ix_citizen_profiles_user_id'), table_name='citizen_profiles')
    op.drop_table('citizen_profiles')
