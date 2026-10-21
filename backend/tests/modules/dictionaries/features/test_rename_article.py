import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import BudgetArticle, Category
from sigma.modules.dictionaries.features.errors import (
    BudgetArticleNotFoundError,
    DuplicateDictionaryNameError,
)
from sigma.modules.dictionaries.features.rename_article import rename_article
from sigma.modules.dictionaries.repository import BudgetArticleRepository


def test_rename_article_saves_new_name() -> None:
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Авиабилеты", category)
    repository = MagicMock(spec=BudgetArticleRepository)
    repository.get = AsyncMock(return_value=article)
    repository.name_exists = AsyncMock(return_value=False)
    repository.save = AsyncMock()

    renamed_article = asyncio.run(
        rename_article(article.id, "  Железнодорожные билеты  ", repository)
    )

    assert renamed_article is article
    assert article.name == "Железнодорожные билеты"
    repository.name_exists.assert_awaited_once_with(
        "железнодорожные билеты",
        exclude_id=article.id,
    )
    repository.save.assert_awaited_once_with(article)


def test_rename_article_rejects_duplicate_name() -> None:
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Авиабилеты", category)
    repository = MagicMock(spec=BudgetArticleRepository)
    repository.get = AsyncMock(return_value=article)
    repository.name_exists = AsyncMock(return_value=True)
    repository.save = AsyncMock()

    with pytest.raises(DuplicateDictionaryNameError, match="Такси"):
        asyncio.run(rename_article(article.id, "Такси", repository))

    assert article.name == "Авиабилеты"
    repository.save.assert_not_awaited()


def test_rename_article_rejects_unknown_article() -> None:
    article_id = uuid4()
    repository = MagicMock(spec=BudgetArticleRepository)
    repository.get = AsyncMock(return_value=None)
    repository.name_exists = AsyncMock()
    repository.save = AsyncMock()

    with pytest.raises(BudgetArticleNotFoundError, match=str(article_id)):
        asyncio.run(rename_article(article_id, "Такси", repository))

    repository.name_exists.assert_not_awaited()
    repository.save.assert_not_awaited()
