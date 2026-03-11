"""The setup of the database

Revision ID: 77e379b5c9f0
Revises: c480d1d5f04f
Create Date: 2026-03-10 19:08:47.818215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77e379b5c9f0'
down_revision: Union[str, Sequence[str], None] = '0faf91b6b2b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
