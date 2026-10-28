import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import MRP
from sigma.modules.dictionaries.features.errors import MRPNotFoundError
from sigma.modules.dictionaries.features.restore_mrp import restore_mrp
from sigma.modules.dictionaries.repository import MRPRepository


@pytest.mark.parametrize("already_active", [False, True])
def test_restore_mrp_is_idempotent(already_active: bool) -> None:
    mrp = MRP(name="Иванов", is_archived=not already_active)
    repository = MagicMock(spec=MRPRepository)
    repository.get = AsyncMock(return_value=mrp)
    repository.save = AsyncMock()

    result = asyncio.run(restore_mrp(mrp.id, repository))

    assert result is mrp
    assert not mrp.is_archived
    repository.get.assert_awaited_once_with(mrp.id)
    if already_active:
        repository.save.assert_not_awaited()
    else:
        repository.save.assert_awaited_once_with(mrp)


def test_restore_mrp_rejects_unknown_mrp() -> None:
    mrp_id = uuid4()
    repository = MagicMock(spec=MRPRepository)
    repository.get = AsyncMock(return_value=None)
    repository.save = AsyncMock()

    with pytest.raises(MRPNotFoundError) as error:
        asyncio.run(restore_mrp(mrp_id, repository))

    assert error.value.mrp_id == mrp_id
    repository.save.assert_not_awaited()
