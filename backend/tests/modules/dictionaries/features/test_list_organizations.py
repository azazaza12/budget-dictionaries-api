import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sigma.modules.dictionaries.domain import Organization
from sigma.modules.dictionaries.features.list_organizations import list_organizations
from sigma.modules.dictionaries.repository import OrganizationRepository


@pytest.mark.parametrize("include_archived", [False, True])
def test_list_organizations_forwards_archive_filter(include_archived: bool) -> None:
    organizations = [Organization(name="Пример", external_name="ООО «Тестовая Компания»")]
    repository = MagicMock(spec=OrganizationRepository)
    repository.list = AsyncMock(return_value=organizations)

    result = asyncio.run(list_organizations(repository, include_archived=include_archived))

    assert result == organizations
    repository.list.assert_awaited_once_with(include_archived=include_archived)


def test_list_organizations_excludes_archived_by_default() -> None:
    repository = MagicMock(spec=OrganizationRepository)
    repository.list = AsyncMock(return_value=[])

    assert asyncio.run(list_organizations(repository)) == []
    repository.list.assert_awaited_once_with(include_archived=False)
