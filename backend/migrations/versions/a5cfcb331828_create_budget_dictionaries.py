"""create budget dictionaries

Revision ID: a5cfcb331828
Revises:
Create Date: 2026-10-19 14:47:03.480446

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a5cfcb331828"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "budget_categories",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_budget_categories")),
        sa.UniqueConstraint(
            "normalized_name",
            name=op.f("uq_budget_categories_normalized_name"),
        ),
    )
    op.create_table(
        "budget_articles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("category_id", sa.Uuid(), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("normalized_name", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["category_id"],
            ["budget_categories.id"],
            name=op.f("fk_budget_articles_category_id_budget_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_budget_articles")),
        sa.UniqueConstraint(
            "normalized_name",
            name=op.f("uq_budget_articles_normalized_name"),
        ),
    )
    op.create_index(
        op.f("ix_budget_articles_category_id"),
        "budget_articles",
        ["category_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_budget_articles_category_id"),
        table_name="budget_articles",
    )
    op.drop_table("budget_articles")
    op.drop_table("budget_categories")
