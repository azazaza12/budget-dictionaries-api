from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, Text, UniqueConstraint, Uuid, false
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


class DistributionRuleModel(Base):
    __tablename__ = "distribution_rules"
    __table_args__ = (
        UniqueConstraint(
            "cfo_id",
            "budget_article_id",
            name="uq_distribution_rules_cfo_article",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    cfo_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("cfo.id", ondelete="RESTRICT"), nullable=False
    )
    budget_article_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("budget_articles.id", ondelete="RESTRICT"), nullable=False
    )
    mrp_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("mrp.id", ondelete="RESTRICT"), nullable=False
    )


class OrganizationModel(Base):
    __tablename__ = "organizations"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    external_name: Mapped[str] = mapped_column(Text, nullable=False)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    normalized_external_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
