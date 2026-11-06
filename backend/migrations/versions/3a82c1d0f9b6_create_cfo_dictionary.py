"""create CFO dictionary

Revision ID: 3a82c1d0f9b6
Revises: a5cfcb331828
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3a82c1d0f9b6"
down_revision: str | Sequence[str] | None = "a5cfcb331828"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cfo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cfo")),
        sa.UniqueConstraint("normalized_name", name=op.f("uq_cfo_normalized_name")),
    )


def downgrade() -> None:
    op.drop_table("cfo")
