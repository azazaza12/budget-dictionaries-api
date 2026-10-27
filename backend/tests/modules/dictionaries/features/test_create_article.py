import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import ArchivedCategoryError, Category
from sigma.modules.dictionaries.features.create_article import create_article
from sigma.modules.dictionaries.features.errors import (
    CategoryNotFoundError,
    DuplicateDictionaryNameError,
)
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CategoryRepository,
)


def test_create_article_adds_article_to_active_category() -> None:
    category = Category(name="Транспорт")
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=category)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.name_exists = AsyncMock(return_value=False)
    article_repository.add = AsyncMock()

    article = asyncio.run(
        create_article(
            "  АвиаБИЛЕТЫ  ",
            category.id,
            category_repository,
            article_repository,
        )
    )

    assert article.name == "АвиаБИЛЕТЫ"
    assert article.normalized_name == "авиабилеты"
    assert article.category_id == category.id
    article_repository.name_exists.assert_awaited_once_with("авиабилеты")
    article_repository.add.assert_awaited_once_with(article)


def test_create_article_rejects_unknown_category() -> None:
    category_id = uuid4()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=None)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.name_exists = AsyncMock()
    article_repository.add = AsyncMock()

    with pytest.raises(CategoryNotFoundError, match=str(category_id)):
        asyncio.run(
            create_article(
                "Авиабилеты",
                category_id,
                category_repository,
                article_repository,
            )
        )

    article_repository.name_exists.assert_not_awaited()
    article_repository.add.assert_not_awaited()


def test_create_article_rejects_archived_category() -> None:
    category = Category(name="Транспорт", is_archived=True)
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=category)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.name_exists = AsyncMock()
    article_repository.add = AsyncMock()

    with pytest.raises(ArchivedCategoryError, match=str(category.id)):
        asyncio.run(
            create_article(
                "Авиабилеты",
                category.id,
                category_repository,
                article_repository,
            )
        )

    article_repository.name_exists.assert_not_awaited()
    article_repository.add.assert_not_awaited()


def test_create_article_rejects_duplicate_name() -> None:
    category = Category(name="Транспорт")
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=category)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.name_exists = AsyncMock(return_value=True)
    article_repository.add = AsyncMock()

    with pytest.raises(DuplicateDictionaryNameError, match="Авиабилеты"):
        asyncio.run(
            create_article(
                "Авиабилеты",
                category.id,
                category_repository,
                article_repository,
            )
        )

    article_repository.add.assert_not_awaited()
