import asyncio
from unittest.mock import AsyncMock, MagicMock

from sigma.modules.dictionaries.domain import Category
from sigma.modules.dictionaries.features.list_categories import list_categories
from sigma.modules.dictionaries.repository import CategoryRepository


def test_list_categories_requests_active_categories_by_default() -> None:
    categories = [Category(name="Транспорт")]
    repository = MagicMock(spec=CategoryRepository)
    repository.list = AsyncMock(return_value=categories)

    result = asyncio.run(list_categories(repository))

    assert result == categories
    repository.list.assert_awaited_once_with(include_archived=False)


def test_list_categories_can_include_archived_categories() -> None:
    categories = [Category(name="Транспорт", is_archived=True)]
    repository = MagicMock(spec=CategoryRepository)
    repository.list = AsyncMock(return_value=categories)

    result = asyncio.run(list_categories(repository, include_archived=True))

    assert result == categories
    repository.list.assert_awaited_once_with(include_archived=True)
