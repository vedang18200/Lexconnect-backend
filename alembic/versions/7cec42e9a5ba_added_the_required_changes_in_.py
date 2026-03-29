"""Added the required changes in consultation table

Revision ID: 7cec42e9a5ba
Revises: fix_lawyer_reviews_permissions
Create Date: 2026-03-15 16:44:27.983721

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '7cec42e9a5ba'
down_revision: Union[str, Sequence[str], None] = 'fix_lawyer_reviews_permissions'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TABLE consultations ADD COLUMN IF NOT EXISTS case_id INTEGER"
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_consultations_case_id_cases'
            ) THEN
                ALTER TABLE consultations
                ADD CONSTRAINT fk_consultations_case_id_cases
                FOREIGN KEY (case_id) REFERENCES cases (id) ON DELETE SET NULL;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(
        "ALTER TABLE consultations DROP CONSTRAINT IF EXISTS fk_consultations_case_id_cases"
    )
    op.execute("ALTER TABLE consultations DROP COLUMN IF EXISTS case_id")
