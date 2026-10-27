import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sigma.modules.dictionaries.features.create_category import create_category
from sigma.modules.dictionaries.features.errors import DuplicateDictionaryNameError
from sigma.modules.dictionaries.repository import CategoryRepository


def test_create_category_adds_cleaned_category() -> None:
    repository = MagicMock(spec=CategoryRepository)
    repository.name_exists = AsyncMock(return_value=False)
    repository.add = AsyncMock()

    category = asyncio.run(create_category("  ТрансПОРТ  ", repository))

    assert category.name == "ТрансПОРТ"
    assert category.normalized_name == "транспорт"
    repository.name_exists.assert_awaited_once_with("транспорт")
    repository.add.assert_awaited_once_with(category)


def test_create_category_rejects_duplicate_name() -> None:
    repository = MagicMock(spec=CategoryRepository)
    repository.name_exists = AsyncMock(return_value=True)
    repository.add = AsyncMock()

    with pytest.raises(DuplicateDictionaryNameError, match="Транспорт"):
        asyncio.run(create_category("Транспорт", repository))

    repository.add.assert_not_awaited()
