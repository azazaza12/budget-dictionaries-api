import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from sigma.modules.dictionaries.domain import InvalidDictionaryNameError
from sigma.modules.dictionaries.features.create_organization import create_organization
from sigma.modules.dictionaries.features.errors import (
    DuplicateDictionaryNameError,
    DuplicateOrganizationNameIn1CError,
)
from sigma.modules.dictionaries.repository import OrganizationRepository


def test_create_organization_adds_cleaned_organization() -> None:
    repository = MagicMock(spec=OrganizationRepository)
    repository.name_exists = AsyncMock(return_value=False)
    repository.name_in_1c_exists = AsyncMock(return_value=False)
    repository.add = AsyncMock()

    organization = asyncio.run(
        create_organization("  ПриМЕР  ", "  ООО\u00a0«Тестовая   Компания»  ", repository)
    )

    assert organization.name == "ПриМЕР"
    assert organization.name_in_1c == "ООО «Тестовая Компания»"
    assert not organization.is_archived
    repository.name_exists.assert_awaited_once_with("пример")
    repository.name_in_1c_exists.assert_awaited_once_with('ооо "тестовая компания"')
    repository.add.assert_awaited_once_with(organization)


def test_create_organization_rejects_duplicate_name() -> None:
    repository = MagicMock(spec=OrganizationRepository)
    repository.name_exists = AsyncMock(return_value=True)
    repository.name_in_1c_exists = AsyncMock()
    repository.add = AsyncMock()

    with pytest.raises(DuplicateDictionaryNameError) as caught:
        asyncio.run(create_organization("  ПриМЕР  ", "ООО «Тестовая Компания»", repository))

    assert caught.value.name == "ПриМЕР"
    repository.name_exists.assert_awaited_once_with("пример")
    repository.name_in_1c_exists.assert_not_awaited()
    repository.add.assert_not_awaited()


def test_create_organization_rejects_duplicate_name_in_1c() -> None:
    repository = MagicMock(spec=OrganizationRepository)
    repository.name_exists = AsyncMock(return_value=False)
    repository.name_in_1c_exists = AsyncMock(return_value=True)
    repository.add = AsyncMock()

    with pytest.raises(DuplicateOrganizationNameIn1CError) as caught:
        asyncio.run(create_organization("Пример", "  ООО «Тестовая   Компания»  ", repository))

    assert caught.value.name_in_1c == "ООО «Тестовая Компания»"
    repository.name_exists.assert_awaited_once_with("пример")
    repository.name_in_1c_exists.assert_awaited_once_with('ооо "тестовая компания"')
    repository.add.assert_not_awaited()


@pytest.mark.parametrize(
    ("name", "name_in_1c"),
    [(" \t ", "ООО «Тестовая Компания»"), ("Пример", " \t ")],
)
def test_create_organization_rejects_empty_names(name: str, name_in_1c: str) -> None:
    repository = MagicMock(spec=OrganizationRepository)
    repository.name_exists = AsyncMock()
    repository.name_in_1c_exists = AsyncMock()
    repository.add = AsyncMock()

    with pytest.raises(InvalidDictionaryNameError):
        asyncio.run(create_organization(name, name_in_1c, repository))

    repository.name_exists.assert_not_awaited()
    repository.name_in_1c_exists.assert_not_awaited()
    repository.add.assert_not_awaited()
