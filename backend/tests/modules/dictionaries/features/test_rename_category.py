import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import Category
from sigma.modules.dictionaries.features.errors import (
    CategoryNotFoundError,
    DuplicateDictionaryNameError,
)
from sigma.modules.dictionaries.features.rename_category import rename_category
from sigma.modules.dictionaries.repository import CategoryRepository


def test_rename_category_saves_new_name() -> None:
    category = Category(name="Транспорт")
    repository = MagicMock(spec=CategoryRepository)
    repository.get = AsyncMock(return_value=category)
    repository.name_exists = AsyncMock(return_value=False)
    repository.save = AsyncMock()

    renamed_category = asyncio.run(rename_category(category.id, "  Командировки  ", repository))

    assert renamed_category is category
    assert category.name == "Командировки"
    repository.name_exists.assert_awaited_once_with(
        "командировки",
        exclude_id=category.id,
    )
    repository.save.assert_awaited_once_with(category)


def test_rename_category_rejects_duplicate_name() -> None:
    category = Category(name="Транспорт")
    repository = MagicMock(spec=CategoryRepository)
    repository.get = AsyncMock(return_value=category)
    repository.name_exists = AsyncMock(return_value=True)
    repository.save = AsyncMock()

    with pytest.raises(DuplicateDictionaryNameError, match="Командировки"):
        asyncio.run(rename_category(category.id, "Командировки", repository))

    assert category.name == "Транспорт"
    repository.save.assert_not_awaited()


def test_rename_category_rejects_unknown_category() -> None:
    category_id = uuid4()
    repository = MagicMock(spec=CategoryRepository)
    repository.get = AsyncMock(return_value=None)
    repository.name_exists = AsyncMock()
    repository.save = AsyncMock()

    with pytest.raises(CategoryNotFoundError, match=str(category_id)):
        asyncio.run(rename_category(category_id, "Командировки", repository))

    repository.name_exists.assert_not_awaited()
    repository.save.assert_not_awaited()
