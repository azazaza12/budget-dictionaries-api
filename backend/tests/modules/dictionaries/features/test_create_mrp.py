import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sigma.modules.dictionaries.domain import InvalidDictionaryNameError
from sigma.modules.dictionaries.features.create_mrp import create_mrp
from sigma.modules.dictionaries.features.errors import DuplicateDictionaryNameError
from sigma.modules.dictionaries.repository import MRPRepository


def test_create_mrp_adds_cleaned_mrp() -> None:
    repository = MagicMock(spec=MRPRepository)
    repository.name_exists = AsyncMock(return_value=False)
    repository.add = AsyncMock()

    mrp = asyncio.run(create_mrp("  ИВАНОВ   Иван ", repository))

    assert mrp.name == "ИВАНОВ Иван"
    assert mrp.normalized_name == "иванов иван"
    assert not mrp.is_archived
    repository.name_exists.assert_awaited_once_with("иванов иван")
    repository.add.assert_awaited_once_with(mrp)


def test_create_mrp_rejects_duplicate_name() -> None:
    repository = MagicMock(spec=MRPRepository)
    repository.name_exists = AsyncMock(return_value=True)
    repository.add = AsyncMock()

    with pytest.raises(DuplicateDictionaryNameError) as error:
        asyncio.run(create_mrp("  Иванов  ", repository))

    assert error.value.name == "Иванов"
    repository.name_exists.assert_awaited_once_with("иванов")
    repository.add.assert_not_awaited()


def test_create_mrp_rejects_empty_name_before_repository_calls() -> None:
    repository = MagicMock(spec=MRPRepository)
    repository.name_exists = AsyncMock()
    repository.add = AsyncMock()

    with pytest.raises(InvalidDictionaryNameError):
        asyncio.run(create_mrp(" \t\n ", repository))

    repository.name_exists.assert_not_awaited()
    repository.add.assert_not_awaited()
