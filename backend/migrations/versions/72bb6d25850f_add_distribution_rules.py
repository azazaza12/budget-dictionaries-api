"""add distribution rules

Revision ID: 72bb6d25850f
Revises: 91e7f4c2a860
Create Date: 2026-10-30 06:25:46.427928

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "72bb6d25850f"
down_revision: str | Sequence[str] | None = "91e7f4c2a860"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "distribution_rules",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cfo_id", sa.Uuid(), nullable=False),
        sa.Column("budget_article_id", sa.Uuid(), nullable=False),
        sa.Column("mrp_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(
            ["budget_article_id"],
            ["budget_articles.id"],
            name=op.f("fk_distribution_rules_budget_article_id_budget_articles"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["cfo_id"],
            ["cfo.id"],
            name=op.f("fk_distribution_rules_cfo_id_cfo"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["mrp_id"],
            ["mrp.id"],
            name=op.f("fk_distribution_rules_mrp_id_mrp"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_distribution_rules")),
        sa.UniqueConstraint(
            "cfo_id", "budget_article_id", name="uq_distribution_rules_cfo_article"
        ),
    )


def downgrade() -> None:
    op.drop_table("distribution_rules")
