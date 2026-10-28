from sqlalchemy import Table, UniqueConstraint

from sigma.modules.dictionaries.models import BudgetArticleModel, CategoryModel, MRPModel


def test_mrp_model_schema() -> None:
    table = MRPModel.__table__
    assert isinstance(table, Table)

    assert MRPModel.__tablename__ == "mrp"
    assert set(table.columns.keys()) == {"id", "name", "normalized_name", "is_archived"}
    assert table.c.id.primary_key
    assert not table.c.name.nullable
    assert not table.c.normalized_name.nullable
    assert not table.c.is_archived.nullable
    assert table.c.is_archived.default is not None
    assert table.c.is_archived.server_default is not None
    assert str(table.c.is_archived.server_default.arg) == "false"
    unique_constraints = [
        constraint for constraint in table.constraints if isinstance(constraint, UniqueConstraint)
    ]
    assert len(unique_constraints) == 1
    assert unique_constraints[0].name == "uq_mrp_normalized_name"
    assert list(unique_constraints[0].columns.keys()) == ["normalized_name"]


def test_category_model_schema() -> None:
    table = CategoryModel.__table__

    assert CategoryModel.__tablename__ == "budget_categories"
    assert set(table.columns.keys()) == {"id", "name", "normalized_name", "is_archived"}
    assert table.c.id.primary_key
    assert not table.c.name.nullable
    assert not table.c.normalized_name.nullable
    assert table.c.normalized_name.unique
    assert not table.c.is_archived.nullable
    assert table.c.is_archived.default is not None
    assert table.c.is_archived.server_default is not None


def test_budget_article_model_schema() -> None:
    table = BudgetArticleModel.__table__

    assert BudgetArticleModel.__tablename__ == "budget_articles"
    assert set(table.columns.keys()) == {
        "id",
        "name",
        "normalized_name",
        "category_id",
        "is_archived",
    }
    assert table.c.id.primary_key
    assert not table.c.name.nullable
    assert not table.c.normalized_name.nullable
    assert table.c.normalized_name.unique
    assert not table.c.category_id.nullable
    assert table.c.category_id.index
    assert not table.c.is_archived.nullable
    assert table.c.is_archived.default is not None
    assert table.c.is_archived.server_default is not None


def test_budget_article_category_foreign_key_restricts_deletion() -> None:
    foreign_keys = BudgetArticleModel.__table__.c.category_id.foreign_keys

    assert len(foreign_keys) == 1
    foreign_key = next(iter(foreign_keys))
    assert foreign_key.target_fullname == "budget_categories.id"
    assert foreign_key.ondelete == "RESTRICT"
