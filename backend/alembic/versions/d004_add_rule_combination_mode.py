"""add_rule_combination_mode

Revision ID: d004
Revises: d003
Create Date: 2026-06-12

Adds rule_combination_mode (nullable String(20)) to feature_flags so a flag
can opt in to AND combination semantics across its rules (Phase 15, AND-02).
NULL is normalized to 'first_match' at the schema/serialization layer —
existing flags keep byte-identical first-match-wins behavior.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd004'
down_revision: Union[str, None] = 'd003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('feature_flags', sa.Column('rule_combination_mode', sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column('feature_flags', 'rule_combination_mode')
