"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-01-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create calls table
    op.create_table(
        'calls',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('audio_object_key', sa.String(), nullable=False),
        sa.Column('duration_sec', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_calls_status', 'calls', ['status'])
    op.create_index('ix_calls_created_at', 'calls', ['created_at'])

    # Create transcripts table
    op.create_table(
        'transcripts',
        sa.Column('call_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('text', sa.String(), nullable=False),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['call_id'], ['calls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('call_id')
    )

    # Create analyses table
    op.create_table(
        'analyses',
        sa.Column('call_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('sentiment', sa.String(), nullable=False),
        sa.Column('topic', sa.String(), nullable=False),
        sa.Column('problem_resolved', sa.Boolean(), nullable=False),
        sa.Column('summary', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['call_id'], ['calls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('call_id')
    )
    op.create_index('ix_analyses_topic', 'analyses', ['topic'])
    op.create_index('ix_analyses_sentiment', 'analyses', ['sentiment'])


def downgrade() -> None:
    op.drop_index('ix_analyses_sentiment')
    op.drop_index('ix_analyses_topic')
    op.drop_table('analyses')
    op.drop_table('transcripts')
    op.drop_index('ix_calls_created_at')
    op.drop_index('ix_calls_status')
    op.drop_table('calls')

