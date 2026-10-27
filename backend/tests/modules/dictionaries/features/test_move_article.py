import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import ArchivedCategoryError, BudgetArticle, Category
from sigma.modules.dictionaries.features.errors import (
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
)
from sigma.modules.dictionaries.features.move_article import move_article
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CategoryRepository,
)


def test_move_article_saves_new_category() -> None:
    current_category = Category(name="Транспорт")
    target_category = Category(name="Командировки")
    article = BudgetArticle.create("Авиабилеты", current_category)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.get = AsyncMock(return_value=article)
    article_repository.save = AsyncMock()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=target_category)

    moved_article = asyncio.run(
        move_article(
            article.id,
            target_category.id,
            article_repository,
            category_repository,
        )
    )

    assert moved_article is article
    assert article.category_id == target_category.id
    article_repository.save.assert_awaited_once_with(article)


def test_move_article_rejects_unknown_article() -> None:
    article_id = uuid4()
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.get = AsyncMock(return_value=None)
    article_repository.save = AsyncMock()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock()

    with pytest.raises(BudgetArticleNotFoundError, match=str(article_id)):
        asyncio.run(
            move_article(
                article_id,
                uuid4(),
                article_repository,
                category_repository,
            )
        )

    category_repository.get.assert_not_awaited()
    article_repository.save.assert_not_awaited()


def test_move_article_rejects_unknown_target_category() -> None:
    current_category = Category(name="Транспорт")
    article = BudgetArticle.create("Авиабилеты", current_category)
    target_category_id = uuid4()
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.get = AsyncMock(return_value=article)
    article_repository.save = AsyncMock()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=None)

    with pytest.raises(CategoryNotFoundError, match=str(target_category_id)):
        asyncio.run(
            move_article(
                article.id,
                target_category_id,
                article_repository,
                category_repository,
            )
        )

    assert article.category_id == current_category.id
    article_repository.save.assert_not_awaited()


def test_move_article_rejects_archived_target_category() -> None:
    current_category = Category(name="Транспорт")
    target_category = Category(name="Командировки", is_archived=True)
    article = BudgetArticle.create("Авиабилеты", current_category)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    article_repository.get = AsyncMock(return_value=article)
    article_repository.save = AsyncMock()
    category_repository = MagicMock(spec=CategoryRepository)
    category_repository.get = AsyncMock(return_value=target_category)

    with pytest.raises(ArchivedCategoryError, match=str(target_category.id)):
        asyncio.run(
            move_article(
                article.id,
                target_category.id,
                article_repository,
                category_repository,
            )
        )

    assert article.category_id == current_category.id
    article_repository.save.assert_not_awaited()
