"""Merge case details and profile dynamic heads

Revision ID: c4d5e6f7a8b9
Revises: add_case_details_fields, 9b1c2d3e4f5a
Create Date: 2026-04-08 00:10:00.000000

"""
from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c4d5e6f7a8b9"
down_revision: Union[str, Sequence[str], None] = (
    "add_case_details_fields",
    "9b1c2d3e4f5a",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge heads with no schema changes."""
    pass


def downgrade() -> None:
    """Downgrade merge revision with no schema changes."""
    pass
