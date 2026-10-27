import asyncio
from unittest.mock import AsyncMock, MagicMock

from sigma.modules.dictionaries.domain import BudgetArticle, Category
from sigma.modules.dictionaries.features.list_articles import list_articles
from sigma.modules.dictionaries.repository import BudgetArticleRepository


def test_list_articles_can_include_archived_articles() -> None:
    category_1 = Category(name="Транспорт")
    article_1 = BudgetArticle(name="Ремонт", category_id=category_1.id, is_archived=True)
    article_2 = BudgetArticle(name="Техосмотр", category_id=category_1.id)
    category_2 = Category(name="Хоздеятельность")
    article_3 = BudgetArticle(name="Хозтовары", category_id=category_2.id)
    articles = [article_1, article_2, article_3]

    repository = MagicMock(spec=BudgetArticleRepository)
    repository.list = AsyncMock(return_value=articles)

    result = asyncio.run(list_articles(repository, include_archived=True))

    assert result == articles
    repository.list.assert_awaited_once_with(include_archived=True)


def test_list_articles_requests_active_articles_by_default() -> None:
    repository = MagicMock(spec=BudgetArticleRepository)
    repository.list = AsyncMock(return_value=[])

    result = asyncio.run(list_articles(repository))

    assert result == []
    repository.list.assert_awaited_once_with(include_archived=False)
