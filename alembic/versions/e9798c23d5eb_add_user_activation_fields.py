"""add user activation fields

Revision ID: e9798c23d5eb
Revises: 0c15a523a67a
Create Date: 2026-09-15 14:09:13.171350

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e9798c23d5eb'
down_revision: Union[str, Sequence[str], None] = '0c15a523a67a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column(
            'activation_token',
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'activation_token_expires_at',
            sa.DateTime(),
            nullable=True,
        ),
    )
    op.create_unique_constraint(
        'uq_users_activation_token',
        'users',
        ['activation_token'],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        'uq_users_activation_token',
        'users',
        type_='unique',
    )
    op.drop_column('users', 'activation_token_expires_at')
    op.drop_column('users', 'activation_token')
