"""Add profile dynamic fields and notification preferences

Revision ID: 9b1c2d3e4f5a
Revises: 7cec42e9a5ba
Create Date: 2026-04-08 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "9b1c2d3e4f5a"
down_revision: Union[str, Sequence[str], None] = "7cec42e9a5ba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "ALTER TABLE citizen_profiles ADD COLUMN IF NOT EXISTS occupation VARCHAR(255)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id SERIAL PRIMARY KEY,
            user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            email_notifications BOOLEAN DEFAULT TRUE,
            sms_notifications BOOLEAN DEFAULT TRUE,
            case_updates BOOLEAN DEFAULT TRUE,
            consultation_reminders BOOLEAN DEFAULT TRUE,
            payment_alerts BOOLEAN DEFAULT TRUE,
            marketing_emails BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ
        )
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_notification_preferences_user_id ON notification_preferences (user_id)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS ix_notification_preferences_user_id")
    op.execute("DROP TABLE IF EXISTS notification_preferences")
    op.execute("ALTER TABLE citizen_profiles DROP COLUMN IF EXISTS occupation")
