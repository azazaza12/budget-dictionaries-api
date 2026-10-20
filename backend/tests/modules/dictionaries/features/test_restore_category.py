import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import Category
from sigma.modules.dictionaries.features.errors import CategoryNotFoundError
from sigma.modules.dictionaries.features.restore_category import restore_category
from sigma.modules.dictionaries.repository import CategoryRepository


def test_restore_category_saves_active_category() -> None:
    category = Category(name="Транспорт", is_archived=True)
    repository = MagicMock(spec=CategoryRepository)
    repository.get = AsyncMock(return_value=category)
    repository.save = AsyncMock()

    restored_category = asyncio.run(restore_category(category.id, repository))

    assert restored_category is category
    assert not category.is_archived
    repository.save.assert_awaited_once_with(category)


def test_restore_category_does_not_save_active_category() -> None:
    category = Category(name="Транспорт")
    repository = MagicMock(spec=CategoryRepository)
    repository.get = AsyncMock(return_value=category)
    repository.save = AsyncMock()

    restored_category = asyncio.run(restore_category(category.id, repository))

    assert restored_category is category
    repository.save.assert_not_awaited()


def test_restore_category_rejects_unknown_category() -> None:
    category_id = uuid4()
    repository = MagicMock(spec=CategoryRepository)
    repository.get = AsyncMock(return_value=None)
    repository.save = AsyncMock()

    with pytest.raises(CategoryNotFoundError, match=str(category_id)):
        asyncio.run(restore_category(category_id, repository))

    repository.save.assert_not_awaited()
