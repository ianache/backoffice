"""add_test_context

Revision ID: d002
Revises: d001
Create Date: 2026-06-11

Adds test_context (nullable TEXT) to feature_flags and segments so the
Live Simulator can persist a per-flag/segment Test Context example
(Phase 13, SIM-01).
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd002'
down_revision: Union[str, None] = 'd001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('feature_flags', sa.Column('test_context', sa.Text(), nullable=True))
    op.add_column('segments', sa.Column('test_context', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('segments', 'test_context')
    op.drop_column('feature_flags', 'test_context')
