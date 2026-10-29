import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sigma.modules.dictionaries.domain import CFO
from sigma.modules.dictionaries.features.list_cfos import list_cfos
from sigma.modules.dictionaries.repository import CFORepository


@pytest.mark.parametrize("include_archived", [False, True])
def test_list_cfos_forwards_archive_filter(include_archived: bool) -> None:
    cfos = [CFO(name="Закупки")]
    repository = MagicMock(spec=CFORepository)
    repository.list = AsyncMock(return_value=cfos)

    result = asyncio.run(list_cfos(repository, include_archived=include_archived))

    assert result == cfos
    repository.list.assert_awaited_once_with(include_archived=include_archived)


def test_list_cfos_excludes_archived_by_default() -> None:
    repository = MagicMock(spec=CFORepository)
    repository.list = AsyncMock(return_value=[])

    assert asyncio.run(list_cfos(repository)) == []
    repository.list.assert_awaited_once_with(include_archived=False)
