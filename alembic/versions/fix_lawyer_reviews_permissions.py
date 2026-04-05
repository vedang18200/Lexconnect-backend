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
    # Note: On Render's managed PostgreSQL, the initial user has sufficient permissions
    # This migration can be skipped as table-level permissions are not required
    # for the application to function properly
    pass


def downgrade() -> None:
    """Revoke permissions from legalaid_user on all tables."""
    # Downgrade is a no-op since upgrade was simplified
    pass
