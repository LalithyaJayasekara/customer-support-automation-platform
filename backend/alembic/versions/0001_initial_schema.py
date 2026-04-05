"""initial schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-04-05 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0001_initial_schema'
down_revision = None
branch_labels = None
deep_dependencies = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('username', sa.String(), nullable=False, unique=True),
        sa.Column('email', sa.String(), nullable=False, unique=True),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'analysis_runs',
        sa.Column('run_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('total_tickets', sa.Integer(), nullable=False),
        sa.Column('high_priority', sa.Integer(), nullable=False),
        sa.Column('approved', sa.Integer(), nullable=False),
        sa.Column('needs_review', sa.Integer(), nullable=False),
        sa.Column('new_count', sa.Integer(), nullable=False),
        sa.Column('in_review_count', sa.Integer(), nullable=False),
        sa.Column('resolved_count', sa.Integer(), nullable=False),
        sa.Column('metrics_json', sa.JSON(), nullable=False),
    )

    op.create_table(
        'ticket_results',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.Integer(), sa.ForeignKey('analysis_runs.run_id'), nullable=False),
        sa.Column('ticket_id', sa.String(), nullable=False),
        sa.Column('original_text', sa.Text(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('urgency', sa.String(), nullable=False),
        sa.Column('sentiment', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('assigned_team', sa.String(), nullable=False),
        sa.Column('draft_reply', sa.Text(), nullable=False),
        sa.Column('qa_status', sa.String(), nullable=False),
        sa.Column('trace_json', sa.JSON(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('ticket_results')
    op.drop_table('analysis_runs')
    op.drop_table('users')
