"""merge CFO and MRP dictionaries

Revision ID: 91e7f4c2a860
Revises: 3a82c1d0f9b6, 7b4d2e9a610c
"""

from collections.abc import Sequence

revision: str = "91e7f4c2a860"
down_revision: str | Sequence[str] | None = ("3a82c1d0f9b6", "7b4d2e9a610c")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
