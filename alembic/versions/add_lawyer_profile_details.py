"""Add education, credentials, and availability to lawyers

Revision ID: add_lawyer_profile_details
Revises:
Create Date: 2026-04-05 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_lawyer_profile_details'
down_revision = '7cec42e9a5ba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to lawyers table
    op.add_column('lawyers', sa.Column('education', sa.Text(), nullable=True))
    op.add_column('lawyers', sa.Column('credentials', sa.Text(), nullable=True))
    op.add_column('lawyers', sa.Column('bar_council_id', sa.String(100), nullable=True))
    op.add_column('lawyers', sa.Column('availability', sa.String(50), server_default='Available'))


def downgrade() -> None:
    # Remove columns if downgrading
    op.drop_column('lawyers', 'availability')
    op.drop_column('lawyers', 'bar_council_id')
    op.drop_column('lawyers', 'credentials')
    op.drop_column('lawyers', 'education')
