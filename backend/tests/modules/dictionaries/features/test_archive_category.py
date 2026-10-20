import asyncio
from unittest.mock import AsyncMock, MagicMock, call
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import BudgetArticle, Category
from sigma.modules.dictionaries.features.archive_category import archive_category
from sigma.modules.dictionaries.features.errors import CategoryNotFoundError
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CategoryRepository,
)


def test_archive_category_archives_category_and_its_articles() -> None:
    category = Category(name="Транспорт")
    articles = [
        BudgetArticle.create("Авиабилеты", category),
        BudgetArticle.create("Такси", category),
    ]
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=category)
    category_repository.save = AsyncMock()
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.list_by_category = AsyncMock(return_value=articles)
    article_repository.save = AsyncMock()

    archived_category = asyncio.run(
        archive_category(category.id, category_repository, article_repository)
    )

    assert archived_category is category
    assert category.is_archived
    assert all(article.is_archived for article in articles)
    category_repository.save.assert_awaited_once_with(category)
    article_repository.list_by_category.assert_awaited_once_with(category.id)
    assert article_repository.save.await_args_list == [call(article) for article in articles]


def test_archive_category_rejects_unknown_category() -> None:
    category_id = uuid4()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=None)
    category_repository.save = AsyncMock()
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.list_by_category = AsyncMock()
    article_repository.save = AsyncMock()

    with pytest.raises(CategoryNotFoundError, match=str(category_id)):
        asyncio.run(archive_category(category_id, category_repository, article_repository))

    category_repository.save.assert_not_awaited()
    article_repository.list_by_category.assert_not_awaited()
    article_repository.save.assert_not_awaited()
