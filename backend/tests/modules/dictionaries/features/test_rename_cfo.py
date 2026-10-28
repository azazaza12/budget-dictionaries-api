import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import CFO, InvalidDictionaryNameError
from sigma.modules.dictionaries.features.errors import (
    CFONotFoundError,
    DuplicateDictionaryNameError,
)
from sigma.modules.dictionaries.features.rename_cfo import rename_cfo
from sigma.modules.dictionaries.repository import CFORepository


@pytest.mark.parametrize("is_archived", [False, True])
def test_rename_cfo_saves_cleaned_name(is_archived: bool) -> None:
    cfo = CFO(name="Закупки", is_archived=is_archived)
    repository = MagicMock(spec=CFORepository)
    repository.get = AsyncMock(return_value=cfo)
    repository.name_exists = AsyncMock(return_value=False)
    repository.save = AsyncMock()

    result = asyncio.run(rename_cfo(cfo.id, "  Отдел   снабжения ", repository))

    assert result is cfo
    assert cfo.name == "Отдел снабжения"
    assert cfo.is_archived is is_archived
    repository.name_exists.assert_awaited_once_with("отдел снабжения", exclude_id=cfo.id)
    repository.save.assert_awaited_once_with(cfo)


def test_rename_cfo_rejects_duplicate_without_mutation() -> None:
    cfo = CFO(name="Закупки")
    repository = MagicMock(spec=CFORepository)
    repository.get = AsyncMock(return_value=cfo)
    repository.name_exists = AsyncMock(return_value=True)
    repository.save = AsyncMock()

    with pytest.raises(DuplicateDictionaryNameError, match="Снабжение"):
        asyncio.run(rename_cfo(cfo.id, "Снабжение", repository))

    assert cfo.name == "Закупки"
    repository.save.assert_not_awaited()


def test_rename_cfo_rejects_missing_cfo() -> None:
    cfo_id = uuid4()
    repository = MagicMock(spec=CFORepository)
    repository.get = AsyncMock(return_value=None)
    repository.name_exists = AsyncMock()
    repository.save = AsyncMock()

    with pytest.raises(CFONotFoundError, match=str(cfo_id)):
        asyncio.run(rename_cfo(cfo_id, "Снабжение", repository))

    repository.name_exists.assert_not_awaited()
    repository.save.assert_not_awaited()


def test_rename_cfo_rejects_empty_name_without_mutation() -> None:
    cfo = CFO(name="Закупки")
    repository = MagicMock(spec=CFORepository)
    repository.get = AsyncMock(return_value=cfo)
    repository.name_exists = AsyncMock()
    repository.save = AsyncMock()

    with pytest.raises(InvalidDictionaryNameError):
        asyncio.run(rename_cfo(cfo.id, " \t ", repository))

    assert cfo.name == "Закупки"
    repository.name_exists.assert_not_awaited()
    repository.save.assert_not_awaited()
