"""Add case details fields for UI display

Revision ID: add_case_details
Revises: add_lawyer_profile_details
Create Date: 2026-04-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_case_details_fields'
down_revision = 'add_lawyer_profile_details'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add court_name, hearing_date, estimated_completion_date, and case_progress to cases table."""
    op.add_column('cases', sa.Column('court_name', sa.String(255), nullable=True))
    op.add_column('cases', sa.Column('hearing_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cases', sa.Column('estimated_completion_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cases', sa.Column('case_progress', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove the added columns."""
    op.drop_column('cases', 'case_progress')
    op.drop_column('cases', 'estimated_completion_date')
    op.drop_column('cases', 'hearing_date')
    op.drop_column('cases', 'court_name')
