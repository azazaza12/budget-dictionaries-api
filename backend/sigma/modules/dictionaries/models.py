from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Text, Uuid, false
from sqlalchemy.orm import Mapped, mapped_column

from sigma.shared.db import Base


class CategoryModel(Base):
    __tablename__ = "budget_categories"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class MRPModel(Base):
    __tablename__ = "mrp"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class BudgetArticleModel(Base):
    __tablename__ = "budget_articles"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    category_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("budget_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)


class CFOModel(Base):
    __tablename__ = "cfo"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
