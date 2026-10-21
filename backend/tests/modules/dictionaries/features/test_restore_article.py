import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import ArchivedCategoryError, BudgetArticle, Category
from sigma.modules.dictionaries.features.errors import (
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
)
from sigma.modules.dictionaries.features.restore_article import restore_article
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CategoryRepository,
)


def test_restore_article_restores_and_saves_article() -> None:
    category = Category(name="Транспорт")
    article = BudgetArticle(name="Ремонт", category_id=category.id, is_archived=True)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.get = AsyncMock(return_value=article)
    article_repository.save = AsyncMock()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=category)

    restored_article = asyncio.run(
        restore_article(article.id, article_repository, category_repository)
    )

    assert restored_article is article
    assert not article.is_archived
    article_repository.get.assert_awaited_once_with(article.id)
    category_repository.get.assert_awaited_once_with(article.category_id)
    article_repository.save.assert_awaited_once_with(article)


def test_restore_article_does_not_save_active_article() -> None:
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Ремонт", category)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.get = AsyncMock(return_value=article)
    article_repository.save = AsyncMock()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock()

    restored_article = asyncio.run(
        restore_article(article.id, article_repository, category_repository)
    )

    assert restored_article is article
    category_repository.get.assert_not_awaited()
    article_repository.save.assert_not_awaited()


def test_restore_article_rejects_unknown_article() -> None:
    article_id = uuid4()
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.get = AsyncMock(return_value=None)
    article_repository.save = AsyncMock()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock()

    with pytest.raises(BudgetArticleNotFoundError, match=str(article_id)):
        asyncio.run(restore_article(article_id, article_repository, category_repository))

    category_repository.get.assert_not_awaited()
    article_repository.save.assert_not_awaited()


def test_restore_article_rejects_unknown_category() -> None:
    category_id = uuid4()
    article = BudgetArticle(name="Ремонт", category_id=category_id, is_archived=True)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.get = AsyncMock(return_value=article)
    article_repository.save = AsyncMock()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=None)

    with pytest.raises(CategoryNotFoundError, match=str(category_id)):
        asyncio.run(restore_article(article.id, article_repository, category_repository))

    article_repository.save.assert_not_awaited()


def test_restore_article_rejects_archived_category() -> None:
    category = Category(name="Транспорт", is_archived=True)
    article = BudgetArticle(name="Ремонт", category_id=category.id, is_archived=True)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.get = AsyncMock(return_value=article)
    article_repository.save = AsyncMock()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=category)

    with pytest.raises(ArchivedCategoryError, match=str(category.id)):
        asyncio.run(restore_article(article.id, article_repository, category_repository))

    assert article.is_archived
    article_repository.save.assert_not_awaited()
