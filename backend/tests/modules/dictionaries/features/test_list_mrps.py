import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sigma.modules.dictionaries.domain import MRP
from sigma.modules.dictionaries.features.list_mrps import list_mrps
from sigma.modules.dictionaries.repository import MRPRepository


@pytest.mark.parametrize("include_archived", [False, True])
def test_list_mrps_passes_archive_filter(include_archived: bool) -> None:
    mrps = [MRP(name="Иванов", is_archived=include_archived)]
    repository = MagicMock(spec=MRPRepository)
    repository.list = AsyncMock(return_value=mrps)

    result = asyncio.run(list_mrps(repository, include_archived=include_archived))

    assert result is mrps
    repository.list.assert_awaited_once_with(include_archived=include_archived)


def test_list_mrps_excludes_archived_by_default() -> None:
    repository = MagicMock(spec=MRPRepository)
    repository.list = AsyncMock(return_value=[])

    assert asyncio.run(list_mrps(repository)) == []
    repository.list.assert_awaited_once_with(include_archived=False)
