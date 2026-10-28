import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from sigma.modules.dictionaries.domain import CFO, BudgetArticle, Category
from sigma.modules.dictionaries.models import BudgetArticleModel, CategoryModel, CFOModel
from sigma.modules.dictionaries.repository import (
    SqlAlchemyBudgetArticleRepository,
    SqlAlchemyCategoryRepository,
    SqlAlchemyCFORepository,
)


def test_get_missing_cfo_returns_none() -> None:
    session = MagicMock(spec=AsyncSession)
    session.get = AsyncMock(return_value=None)
    repository = SqlAlchemyCFORepository(session)

    assert asyncio.run(repository.get(uuid4())) is None


@pytest.mark.parametrize("include_archived", [False, True])
def test_list_cfos_maps_models_and_filters_archived(include_archived: bool) -> None:
    cfo_id = uuid4()
    result = MagicMock()
    result.all.return_value = [
        CFOModel(
            id=cfo_id,
            name="Закупки",
            normalized_name="закупки",
            is_archived=False,
        )
    ]
    session = MagicMock(spec=AsyncSession)
    session.scalars = AsyncMock(return_value=result)
    repository = SqlAlchemyCFORepository(session)

    cfos = asyncio.run(repository.list(include_archived=include_archived))

    assert cfos == [CFO(id=cfo_id, name="Закупки")]
    statement = str(session.scalars.await_args.args[0])
    assert ("cfo.is_archived IS false" in statement) is not include_archived
    assert "ORDER BY cfo.normalized_name, cfo.id" in statement


@pytest.mark.parametrize("exclude_self", [False, True])
@pytest.mark.parametrize("exists", [False, True])
def test_cfo_name_existence_query(exclude_self: bool, exists: bool) -> None:
    session = MagicMock(spec=AsyncSession)
    session.scalar = AsyncMock(return_value=exists)
    repository = SqlAlchemyCFORepository(session)
    excluded_id = uuid4() if exclude_self else None

    result = asyncio.run(repository.name_exists("закупки", exclude_id=excluded_id))

    assert result is exists
    statement = session.scalar.await_args.args[0]
    sql = str(statement)
    assert "EXISTS (SELECT cfo.id" in sql
    assert "cfo.normalized_name =" in sql
    assert "is_archived" not in sql
    assert ("cfo.id !=" in sql) is exclude_self
    assert "закупки" in statement.compile().params.values()
    if excluded_id is not None:
        assert excluded_id in statement.compile().params.values()


def test_get_category_maps_model_to_domain() -> None:
    category_id = uuid4()
    session = MagicMock(spec=AsyncSession)
    session.get = AsyncMock(
        return_value=CategoryModel(
            id=category_id,
            name="Транспорт",
            normalized_name="транспорт",
            is_archived=True,
        )
    )
    repository = SqlAlchemyCategoryRepository(session)

    category = asyncio.run(repository.get(category_id))

    assert category == Category(id=category_id, name="Транспорт", is_archived=True)


def test_add_category_maps_domain_to_model() -> None:
    session = MagicMock(spec=AsyncSession)
    repository = SqlAlchemyCategoryRepository(session)
    category = Category(name="  ТрансПОРТ ")

    asyncio.run(repository.add(category))

    model = session.add.call_args.args[0]
    assert isinstance(model, CategoryModel)
    assert model.id == category.id
    assert model.name == "ТрансПОРТ"
    assert model.normalized_name == "транспорт"
    assert not model.is_archived


def test_save_category_merges_model() -> None:
    session = MagicMock(spec=AsyncSession)
    session.merge = AsyncMock()
    repository = SqlAlchemyCategoryRepository(session)
    category = Category(name="Транспорт")
    category.rename("Командировки")

    asyncio.run(repository.save(category))

    model = session.merge.await_args.args[0]
    assert isinstance(model, CategoryModel)
    assert model.name == "Командировки"
    assert model.normalized_name == "командировки"


def test_get_article_maps_model_to_domain() -> None:
    article_id = uuid4()
    category_id = uuid4()
    session = MagicMock(spec=AsyncSession)
    session.get = AsyncMock(
        return_value=BudgetArticleModel(
            id=article_id,
            name="Авиабилеты",
            normalized_name="авиабилеты",
            category_id=category_id,
            is_archived=True,
        )
    )
    repository = SqlAlchemyBudgetArticleRepository(session)

    article = asyncio.run(repository.get(article_id))

    assert article == BudgetArticle(
        id=article_id,
        name="Авиабилеты",
        category_id=category_id,
        is_archived=True,
    )


def test_add_article_maps_domain_to_model() -> None:
    session = MagicMock(spec=AsyncSession)
    repository = SqlAlchemyBudgetArticleRepository(session)
    category = Category(name="Транспорт")
    article = BudgetArticle.create("  АвиаБИЛЕТЫ ", category)

    asyncio.run(repository.add(article))

    model = session.add.call_args.args[0]
    assert isinstance(model, BudgetArticleModel)
    assert model.id == article.id
    assert model.name == "АвиаБИЛЕТЫ"
    assert model.normalized_name == "авиабилеты"
    assert model.category_id == category.id
    assert not model.is_archived


def test_save_article_merges_model() -> None:
    session = MagicMock(spec=AsyncSession)
    session.merge = AsyncMock()
    repository = SqlAlchemyBudgetArticleRepository(session)
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Авиабилеты", category)
    article.rename("Железнодорожные билеты")

    asyncio.run(repository.save(article))

    model = session.merge.await_args.args[0]
    assert isinstance(model, BudgetArticleModel)
    assert model.name == "Железнодорожные билеты"
    assert model.normalized_name == "железнодорожные билеты"
    assert model.category_id == category.id


def test_category_name_existence_uses_scalar_query() -> None:
    session = MagicMock(spec=AsyncSession)
    session.scalar = AsyncMock(return_value=True)
    repository = SqlAlchemyCategoryRepository(session)

    exists = asyncio.run(repository.name_exists("транспорт"))

    assert exists
    session.scalar.assert_awaited_once()


def test_article_name_existence_uses_scalar_query() -> None:
    session = MagicMock(spec=AsyncSession)
    session.scalar = AsyncMock(return_value=True)
    repository = SqlAlchemyBudgetArticleRepository(session)

    exists = asyncio.run(repository.name_exists("авиабилеты"))

    assert exists
    session.scalar.assert_awaited_once()


def test_list_articles_by_category_maps_models_to_domain() -> None:
    category_id = uuid4()
    article_id = uuid4()
    result = MagicMock()
    result.all.return_value = [
        BudgetArticleModel(
            id=article_id,
            name="Авиабилеты",
            normalized_name="авиабилеты",
            category_id=category_id,
            is_archived=False,
        )
    ]
    session = MagicMock(spec=AsyncSession)
    session.scalars = AsyncMock(return_value=result)
    repository = SqlAlchemyBudgetArticleRepository(session)

    articles = asyncio.run(repository.list_by_category(category_id))

    assert articles == [
        BudgetArticle(
            id=article_id,
            name="Авиабилеты",
            category_id=category_id,
            is_archived=False,
        )
    ]
