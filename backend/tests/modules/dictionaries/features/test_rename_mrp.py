import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import MRP, InvalidDictionaryNameError
from sigma.modules.dictionaries.features.errors import (
    DuplicateDictionaryNameError,
    MRPNotFoundError,
)
from sigma.modules.dictionaries.features.rename_mrp import rename_mrp
from sigma.modules.dictionaries.repository import MRPRepository


@pytest.mark.parametrize("is_archived", [False, True])
def test_rename_mrp_saves_new_name(is_archived: bool) -> None:
    mrp = MRP(name="Иванов", is_archived=is_archived)
    repository = MagicMock(spec=MRPRepository)
    repository.get = AsyncMock(return_value=mrp)
    repository.name_exists = AsyncMock(return_value=False)
    repository.save = AsyncMock()

    result = asyncio.run(rename_mrp(mrp.id, "  ПЕТРОВ   Пётр ", repository))

    assert result is mrp
    assert mrp.name == "ПЕТРОВ Пётр"
    assert mrp.normalized_name == "петров пётр"
    assert mrp.is_archived is is_archived
    repository.get.assert_awaited_once_with(mrp.id)
    repository.name_exists.assert_awaited_once_with("петров пётр", exclude_id=mrp.id)
    repository.save.assert_awaited_once_with(mrp)


def test_rename_mrp_rejects_duplicate_without_mutation() -> None:
    mrp = MRP(name="Иванов")
    repository = MagicMock(spec=MRPRepository)
    repository.get = AsyncMock(return_value=mrp)
    repository.name_exists = AsyncMock(return_value=True)
    repository.save = AsyncMock()

    with pytest.raises(DuplicateDictionaryNameError):
        asyncio.run(rename_mrp(mrp.id, "Петров", repository))

    assert mrp.name == "Иванов"
    repository.name_exists.assert_awaited_once_with("петров", exclude_id=mrp.id)
    repository.save.assert_not_awaited()


def test_rename_mrp_rejects_unknown_mrp() -> None:
    mrp_id = uuid4()
    repository = MagicMock(spec=MRPRepository)
    repository.get = AsyncMock(return_value=None)
    repository.name_exists = AsyncMock()
    repository.save = AsyncMock()

    with pytest.raises(MRPNotFoundError) as error:
        asyncio.run(rename_mrp(mrp_id, "Петров", repository))

    assert error.value.mrp_id == mrp_id
    repository.name_exists.assert_not_awaited()
    repository.save.assert_not_awaited()


def test_rename_mrp_rejects_empty_name_without_mutation() -> None:
    mrp = MRP(name="Иванов")
    repository = MagicMock(spec=MRPRepository)
    repository.get = AsyncMock(return_value=mrp)
    repository.name_exists = AsyncMock()
    repository.save = AsyncMock()

    with pytest.raises(InvalidDictionaryNameError):
        asyncio.run(rename_mrp(mrp.id, " \t ", repository))

    assert mrp.name == "Иванов"
    repository.name_exists.assert_not_awaited()
    repository.save.assert_not_awaited()
