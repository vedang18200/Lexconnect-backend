"""Add lawyer professional tables

Revision ID: lawyer_features_001
Revises: citizen_features_001
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'lawyer_features_001'
down_revision = 'citizen_features_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create lawyer_credential table
    op.create_table(
        'lawyer_credential',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('license_number', sa.String(255), nullable=False),
        sa.Column('license_state', sa.String(100), nullable=False),
        sa.Column('bar_association', sa.String(255), nullable=True),
        sa.Column('bar_admission_year', sa.Integer(), nullable=True),
        sa.Column('qualifications', postgresql.JSON(), nullable=True),
        sa.Column('court_admissions', postgresql.JSON(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verification_documents', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['lawyer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('lawyer_id')
    )
    op.create_index('idx_lawyer_credential_lawyer_id', 'lawyer_credential', ['lawyer_id'])

    # Create lawyer_availability table
    op.create_table(
        'lawyer_availability',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),  # 0-6 (Monday-Sunday)
        sa.Column('start_time', sa.String(5), nullable=False),  # HH:MM
        sa.Column('end_time', sa.String(5), nullable=False),    # HH:MM
        sa.Column('is_available', sa.Boolean(), default=True),
        sa.Column('slot_duration_minutes', sa.Integer(), default=60),
        sa.Column('break_start', sa.String(5), nullable=True),
        sa.Column('break_end', sa.String(5), nullable=True),
        sa.Column('date_specific', sa.Date(), nullable=True),   # For overrides
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['lawyer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_lawyer_availability_lawyer_id', 'lawyer_availability', ['lawyer_id'])
    op.create_index('idx_lawyer_availability_day', 'lawyer_availability', ['lawyer_id', 'day_of_week'])

    # Create invoice table
    op.create_table(
        'invoice',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('citizen_id', sa.Integer(), nullable=True),
        sa.Column('consultation_id', sa.Integer(), nullable=True),
        sa.Column('case_id', sa.Integer(), nullable=True),
        sa.Column('invoice_number', sa.String(50), nullable=False, unique=True),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('tax_percentage', sa.Numeric(precision=5, scale=2), default=0),
        sa.Column('tax_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', sa.String(50), default='draft'),  # draft, issued, paid, overdue, cancelled
        sa.Column('issued_at', sa.DateTime(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['lawyer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['citizen_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['consultation_id'], ['consultations.id'], ),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_invoice_lawyer_id', 'invoice', ['lawyer_id'])
    op.create_index('idx_invoice_citizen_id', 'invoice', ['citizen_id'])
    op.create_index('idx_invoice_status', 'invoice', ['status'])
    op.create_index('idx_invoice_created_at', 'invoice', ['created_at'])

    # Create document_template table
    op.create_table(
        'document_template',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_type', sa.String(100), nullable=False),  # contract, agreement, petition, etc
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['lawyer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_document_template_lawyer_id', 'document_template', ['lawyer_id'])
    op.create_index('idx_document_template_type', 'document_template', ['template_type'])

    # Create case_note table
    op.create_table(
        'case_note',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('note_type', sa.String(50), nullable=False),  # progress, action_item, deadline
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_private', sa.Boolean(), default=True),
        sa.Column('priority', sa.String(50), default='medium'),  # low, medium, high
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), default=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.ForeignKeyConstraint(['lawyer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_case_note_case_id', 'case_note', ['case_id'])
    op.create_index('idx_case_note_lawyer_id', 'case_note', ['lawyer_id'])
    op.create_index('idx_case_note_is_completed', 'case_note', ['is_completed'])


def downgrade() -> None:
    op.drop_index('idx_case_note_is_completed', table_name='case_note')
    op.drop_index('idx_case_note_lawyer_id', table_name='case_note')
    op.drop_index('idx_case_note_case_id', table_name='case_note')
    op.drop_table('case_note')

    op.drop_index('idx_document_template_type', table_name='document_template')
    op.drop_index('idx_document_template_lawyer_id', table_name='document_template')
    op.drop_table('document_template')

    op.drop_index('idx_invoice_created_at', table_name='invoice')
    op.drop_index('idx_invoice_status', table_name='invoice')
    op.drop_index('idx_invoice_citizen_id', table_name='invoice')
    op.drop_index('idx_invoice_lawyer_id', table_name='invoice')
    op.drop_table('invoice')

    op.drop_index('idx_lawyer_availability_day', table_name='lawyer_availability')
    op.drop_index('idx_lawyer_availability_lawyer_id', table_name='lawyer_availability')
    op.drop_table('lawyer_availability')

    op.drop_index('idx_lawyer_credential_lawyer_id', table_name='lawyer_credential')
    op.drop_table('lawyer_credential')
