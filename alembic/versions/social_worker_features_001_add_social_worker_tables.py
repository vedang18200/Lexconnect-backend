"""Add social worker tables

Revision ID: social_worker_features_001
Revises: lawyer_features_001
Create Date: 2024-01-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'social_worker_features_001'
down_revision = 'lawyer_features_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create agency table
    op.create_table(
        'agencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('address', sa.String(500), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('contact_person', sa.String(255), nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_agencies_id', 'agencies', ['id'])

    # Create social_worker_profiles table
    op.create_table(
        'social_worker_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, unique=True),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('license_number', sa.String(255), nullable=True),
        sa.Column('specialization', sa.String(255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('total_referrals', sa.Integer(), default=0),
        sa.Column('successful_referrals', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_social_worker_profiles_user_id', 'social_worker_profiles', ['user_id'])
    op.create_index('idx_social_worker_profiles_agency_id', 'social_worker_profiles', ['agency_id'])

    # Create referrals table
    op.create_table(
        'referrals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('social_worker_id', sa.Integer(), nullable=False),
        sa.Column('lawyer_id', sa.Integer(), nullable=False),
        sa.Column('citizen_id', sa.Integer(), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=True),
        sa.Column('referral_reason', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='pending'),  # pending, accepted, in_progress, completed, closed
        sa.Column('case_category', sa.String(255), nullable=True),
        sa.Column('outcome', sa.String(50), nullable=True),  # resolved, ongoing, unsuccessful, etc
        sa.Column('outcome_notes', sa.Text(), nullable=True),
        sa.Column('referral_date', sa.DateTime(), default=sa.func.now()),
        sa.Column('accepted_date', sa.DateTime(), nullable=True),
        sa.Column('completed_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['social_worker_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['lawyer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['citizen_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['case_id'], ['cases.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_referrals_social_worker_id', 'referrals', ['social_worker_id'])
    op.create_index('idx_referrals_lawyer_id', 'referrals', ['lawyer_id'])
    op.create_index('idx_referrals_citizen_id', 'referrals', ['citizen_id'])
    op.create_index('idx_referrals_status', 'referrals', ['status'])
    op.create_index('idx_referrals_created_at', 'referrals', ['created_at'])


def downgrade() -> None:
    op.drop_index('idx_referrals_created_at', table_name='referrals')
    op.drop_index('idx_referrals_status', table_name='referrals')
    op.drop_index('idx_referrals_citizen_id', table_name='referrals')
    op.drop_index('idx_referrals_lawyer_id', table_name='referrals')
    op.drop_index('idx_referrals_social_worker_id', table_name='referrals')
    op.drop_table('referrals')

    op.drop_index('idx_social_worker_profiles_agency_id', table_name='social_worker_profiles')
    op.drop_index('idx_social_worker_profiles_user_id', table_name='social_worker_profiles')
    op.drop_table('social_worker_profiles')

    op.drop_index('idx_agencies_id', table_name='agencies')
    op.drop_table('agencies')
