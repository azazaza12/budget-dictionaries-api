import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import CFO
from sigma.modules.dictionaries.features.archive_cfo import archive_cfo
from sigma.modules.dictionaries.features.errors import CFONotFoundError
from sigma.modules.dictionaries.repository import CFORepository


@pytest.mark.parametrize("is_archived", [False, True])
def test_archive_cfo_is_idempotent(is_archived: bool) -> None:
    cfo = CFO(name="Закупки", is_archived=is_archived)
    repository = MagicMock(spec=CFORepository)
    repository.get = AsyncMock(return_value=cfo)
    repository.save = AsyncMock()

    result = asyncio.run(archive_cfo(cfo.id, repository))

    assert result is cfo
    assert cfo.is_archived
    repository.get.assert_awaited_once_with(cfo.id)
    if is_archived:
        repository.save.assert_not_awaited()
    else:
        repository.save.assert_awaited_once_with(cfo)


def test_archive_cfo_rejects_missing_cfo() -> None:
    cfo_id = uuid4()
    repository = MagicMock(spec=CFORepository)
    repository.get = AsyncMock(return_value=None)
    repository.save = AsyncMock()

    with pytest.raises(CFONotFoundError, match=str(cfo_id)):
        asyncio.run(archive_cfo(cfo_id, repository))

    repository.save.assert_not_awaited()
