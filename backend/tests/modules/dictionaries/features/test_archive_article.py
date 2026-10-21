import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import BudgetArticle, Category
from sigma.modules.dictionaries.features.archive_article import archive_article
from sigma.modules.dictionaries.features.errors import BudgetArticleNotFoundError
from sigma.modules.dictionaries.repository import BudgetArticleRepository


def test_archive_article_archives_and_saves_article() -> None:
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Ремонт", category)
    repository = MagicMock(spec=BudgetArticleRepository)
    repository.get = AsyncMock(return_value=article)
    repository.save = AsyncMock()

    archived_article = asyncio.run(archive_article(article.id, repository))

    assert archived_article is article
    assert article.is_archived
    repository.get.assert_awaited_once_with(article.id)
    repository.save.assert_awaited_once_with(article)


def test_archive_article_does_not_save_archived_article() -> None:
    category = Category(name="Транспорт")
    article = BudgetArticle(name="Ремонт", category_id=category.id, is_archived=True)
    repository = MagicMock(spec=BudgetArticleRepository)
    repository.get = AsyncMock(return_value=article)
    repository.save = AsyncMock()

    archived_article = asyncio.run(archive_article(article.id, repository))

    assert archived_article is article
    repository.save.assert_not_awaited()


def test_archive_article_rejects_unknown_article() -> None:
    article_id = uuid4()
    repository = MagicMock(spec=BudgetArticleRepository)
    repository.get = AsyncMock(return_value=None)
    repository.save = AsyncMock()

    with pytest.raises(BudgetArticleNotFoundError, match=str(article_id)):
        asyncio.run(archive_article(article_id, repository))

    repository.save.assert_not_awaited()
