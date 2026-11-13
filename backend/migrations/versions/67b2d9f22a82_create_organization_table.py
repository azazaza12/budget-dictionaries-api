"""create organization table

Revision ID: 67b2d9f22a82
Revises: 91e7f4c2a860
Create Date: 2026-11-09 15:55:57.502067

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "67b2d9f22a82"
down_revision: str | Sequence[str] | None = "91e7f4c2a860"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("external_name", sa.Text(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("normalized_external_name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
        sa.UniqueConstraint("normalized_name", name=op.f("uq_organizations_normalized_name")),
        sa.UniqueConstraint(
            "normalized_external_name", name=op.f("uq_organizations_normalized_external_name")
        ),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    op.drop_table("organizations")
    # ### end Alembic commands ###
