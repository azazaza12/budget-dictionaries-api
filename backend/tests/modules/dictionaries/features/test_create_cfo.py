import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sigma.modules.dictionaries.domain import InvalidDictionaryNameError
from sigma.modules.dictionaries.features.create_cfo import create_cfo
from sigma.modules.dictionaries.features.errors import DuplicateDictionaryNameError
from sigma.modules.dictionaries.repository import CFORepository


def test_create_cfo_adds_cleaned_cfo() -> None:
    repository = MagicMock(spec=CFORepository)
    repository.name_exists = AsyncMock(return_value=False)
    repository.add = AsyncMock()

    cfo = asyncio.run(create_cfo("  Отдел   ЗАКУПОК ", repository))

    assert cfo.name == "Отдел ЗАКУПОК"
    assert cfo.normalized_name == "отдел закупок"
    assert not cfo.is_archived
    repository.name_exists.assert_awaited_once_with("отдел закупок")
    repository.add.assert_awaited_once_with(cfo)


def test_create_cfo_rejects_duplicate_name() -> None:
    repository = MagicMock(spec=CFORepository)
    repository.name_exists = AsyncMock(return_value=True)
    repository.add = AsyncMock()

    with pytest.raises(DuplicateDictionaryNameError, match="Закупки"):
        asyncio.run(create_cfo("Закупки", repository))

    repository.add.assert_not_awaited()


def test_create_cfo_rejects_empty_name() -> None:
    repository = MagicMock(spec=CFORepository)
    repository.name_exists = AsyncMock()
    repository.add = AsyncMock()

    with pytest.raises(InvalidDictionaryNameError):
        asyncio.run(create_cfo(" \t ", repository))

    repository.name_exists.assert_not_awaited()
    repository.add.assert_not_awaited()
