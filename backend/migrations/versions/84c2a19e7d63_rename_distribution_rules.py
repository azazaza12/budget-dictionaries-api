"""rename distribution rules

Revision ID: 84c2a19e7d63
Revises: 72bb6d25850f
Create Date: 2026-11-06

"""

from collections.abc import Sequence

from alembic import op

revision: str = "84c2a19e7d63"
down_revision: str | Sequence[str] | None = "72bb6d25850f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _rename_constraints(table: str, old: str, new: str) -> None:
    for prefix, suffix in (
        ("pk", ""),
        ("uq", "_cfo_article"),
        ("fk", "_budget_article_id_budget_articles"),
        ("fk", "_cfo_id_cfo"),
        ("fk", "_mrp_id_mrp"),
    ):
        op.execute(
            f'ALTER TABLE "{table}" RENAME CONSTRAINT "{prefix}_{old}{suffix}" '
            f'TO "{prefix}_{new}{suffix}"'
        )


def upgrade() -> None:
    op.rename_table("savings_distribution_rules", "distribution_rules")
    _rename_constraints("distribution_rules", "savings_distribution_rules", "distribution_rules")


def downgrade() -> None:
    _rename_constraints("distribution_rules", "distribution_rules", "savings_distribution_rules")
    op.rename_table("distribution_rules", "savings_distribution_rules")
