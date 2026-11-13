import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import Organization
from sigma.modules.dictionaries.features.archive_organization import archive_organization
from sigma.modules.dictionaries.features.errors import OrganizationNotFoundError
from sigma.modules.dictionaries.repository import OrganizationRepository


@pytest.mark.parametrize("is_archived", [False, True])
def test_archive_organization_is_idempotent(is_archived: bool) -> None:
    organization = Organization(
        name="Пример", external_name="ООО «Тестовая Компания»", is_archived=is_archived
    )
    repository = MagicMock(spec=OrganizationRepository)
    repository.get = AsyncMock(return_value=organization)
    repository.save = AsyncMock()

    result = asyncio.run(archive_organization(organization.id, repository))

    assert result is organization
    assert organization.is_archived
    repository.get.assert_awaited_once_with(organization.id)
    if is_archived:
        repository.save.assert_not_awaited()
    else:
        repository.save.assert_awaited_once_with(organization)


def test_archive_organization_rejects_missing_organization() -> None:
    organization_id = uuid4()
    repository = MagicMock(spec=OrganizationRepository)
    repository.get = AsyncMock(return_value=None)
    repository.save = AsyncMock()

    with pytest.raises(OrganizationNotFoundError) as caught:
        asyncio.run(archive_organization(organization_id, repository))

    assert caught.value.organization_id == organization_id
    repository.get.assert_awaited_once_with(organization_id)
    repository.save.assert_not_awaited()
