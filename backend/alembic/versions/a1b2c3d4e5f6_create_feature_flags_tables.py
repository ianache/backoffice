"""create_feature_flags_tables

Revision ID: a1b2c3d4e5f6
Revises: f977f6d434f7
Create Date: 2026-06-07 16:09:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f977f6d434f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('scope', sa.String(length=20), nullable=False),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.Column('product_id', sa.String(length=100), nullable=True),
        sa.Column('company_id', sa.String(length=100), nullable=True),
        sa.Column('enabled', sa.SmallInteger(), server_default='1', nullable=False),
        sa.Column('default_val', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('complex', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('ttl', sa.Integer(), nullable=True),
        sa.Column('environment', sa.String(length=20), server_default='production', nullable=False),
        sa.Column('rollout', sa.Integer(), server_default='100', nullable=False),
        sa.Column('rules', sa.Text(), nullable=True),    # JSON array serialized as TEXT — MySQL 5.6 safe
        sa.Column('tags', sa.Text(), nullable=True),     # JSON array serialized as TEXT — MySQL 5.6 safe
        sa.Column('created_by', sa.String(length=36), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_feature_flags_name', 'feature_flags', ['name'], unique=False)
    op.create_index('ix_feature_flags_tenant_id', 'feature_flags', ['tenant_id'], unique=False)

    op.create_table(
        'segments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.Column('members', sa.Text(), nullable=True),  # JSON array of user UUIDs as TEXT — MySQL 5.6 safe
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_segments_name', 'segments', ['name'], unique=False)
    op.create_index('ix_segments_tenant_id', 'segments', ['tenant_id'], unique=False)

    op.create_table(
        'flag_segments',
        sa.Column('flag_id', sa.Integer(), nullable=False),
        sa.Column('segment_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['flag_id'], ['feature_flags.id']),
        sa.ForeignKeyConstraint(['segment_id'], ['segments.id']),
        sa.PrimaryKeyConstraint('flag_id', 'segment_id'),
    )


def downgrade() -> None:
    op.drop_table('flag_segments')
    op.drop_index('ix_segments_tenant_id', table_name='segments')
    op.drop_index('ix_segments_name', table_name='segments')
    op.drop_table('segments')
    op.drop_index('ix_feature_flags_tenant_id', table_name='feature_flags')
    op.drop_index('ix_feature_flags_name', table_name='feature_flags')
    op.drop_table('feature_flags')
