import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import InvalidDictionaryNameError, Organization
from sigma.modules.dictionaries.features.errors import (
    DuplicateDictionaryNameError,
    DuplicateOrganizationNameIn1CError,
    OrganizationNotFoundError,
)
from sigma.modules.dictionaries.features.rename_organization import rename_organization
from sigma.modules.dictionaries.repository import OrganizationRepository


@pytest.fixture
def repository() -> MagicMock:
    repository = MagicMock(spec=OrganizationRepository)
    repository.get = AsyncMock()
    repository.name_exists = AsyncMock(return_value=False)
    repository.name_in_1c_exists = AsyncMock(return_value=False)
    repository.save = AsyncMock()
    return repository


@pytest.mark.parametrize("is_archived", [False, True])
def test_rename_organization_saves_cleaned_names(is_archived: bool, repository: MagicMock) -> None:
    organization = Organization(name="Образец", name_in_1c="ООО «Образец»", is_archived=is_archived)
    organization_id = organization.id
    repository.get.return_value = organization

    result = asyncio.run(
        rename_organization(
            organization_id, "  ПриМЕР\u00a0 ", "  ООО «Тестовая   Компания»  ", repository
        )
    )

    assert result is organization
    assert organization.id == organization_id
    assert organization.name == "ПриМЕР"
    assert organization.name_in_1c == "ООО «Тестовая Компания»"
    assert organization.is_archived is is_archived
    repository.get.assert_awaited_once_with(organization_id)
    repository.name_exists.assert_awaited_once_with("пример", exclude_id=organization_id)
    repository.name_in_1c_exists.assert_awaited_once_with(
        'ооо "тестовая компания"', exclude_id=organization_id
    )
    repository.save.assert_awaited_once_with(organization)


@pytest.mark.parametrize(
    ("new_name", "new_name_in_1c", "normalized_name", "normalized_name_in_1c"),
    [
        ("Образец", "ООО «Образец»", "образец", 'ооо "образец"'),
        ("Пример", "ООО «Образец»", "пример", 'ооо "образец"'),
        ("Образец", "ООО «Пример»", "образец", 'ооо "пример"'),
        ("ОБРАЗЕЦ", 'ООО "Образец"', "образец", 'ооо "образец"'),
    ],
)
def test_rename_organization_excludes_self_for_both_names(
    new_name: str,
    new_name_in_1c: str,
    normalized_name: str,
    normalized_name_in_1c: str,
    repository: MagicMock,
) -> None:
    organization = Organization(name="Образец", name_in_1c="ООО «Образец»")
    repository.get.return_value = organization

    result = asyncio.run(rename_organization(organization.id, new_name, new_name_in_1c, repository))

    assert result is organization
    assert organization.name == new_name
    assert organization.name_in_1c == new_name_in_1c
    repository.name_exists.assert_awaited_once_with(normalized_name, exclude_id=organization.id)
    repository.name_in_1c_exists.assert_awaited_once_with(
        normalized_name_in_1c, exclude_id=organization.id
    )
    repository.save.assert_awaited_once_with(organization)


@pytest.mark.parametrize("duplicate_in_1c", [False, True])
def test_rename_organization_rejects_duplicates_without_mutation(
    duplicate_in_1c: bool, repository: MagicMock
) -> None:
    organization = Organization(name="Образец", name_in_1c="ООО «Образец»")
    repository.get.return_value = organization
    repository.name_exists.return_value = not duplicate_in_1c
    repository.name_in_1c_exists.return_value = duplicate_in_1c
    error_type = (
        DuplicateOrganizationNameIn1CError if duplicate_in_1c else DuplicateDictionaryNameError
    )

    with pytest.raises(error_type) as caught:
        asyncio.run(rename_organization(organization.id, "Пример", "ООО «Пример»", repository))

    assert organization.name == "Образец"
    assert organization.name_in_1c == "ООО «Образец»"
    repository.name_exists.assert_awaited_once_with("пример", exclude_id=organization.id)
    if duplicate_in_1c:
        assert isinstance(caught.value, DuplicateOrganizationNameIn1CError)
        assert caught.value.name_in_1c == "ООО «Пример»"
        repository.name_in_1c_exists.assert_awaited_once_with(
            'ооо "пример"', exclude_id=organization.id
        )
    else:
        assert isinstance(caught.value, DuplicateDictionaryNameError)
        assert caught.value.name == "Пример"
        repository.name_in_1c_exists.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.parametrize("empty_in_1c", [False, True])
def test_rename_organization_rejects_empty_names_without_mutation(
    empty_in_1c: bool, repository: MagicMock
) -> None:
    organization = Organization(name="Образец", name_in_1c="ООО «Образец»")
    repository.get.return_value = organization
    new_name = "Пример" if empty_in_1c else " \t "
    new_name_in_1c = " \t " if empty_in_1c else "ООО «Пример»"

    with pytest.raises(InvalidDictionaryNameError):
        asyncio.run(rename_organization(organization.id, new_name, new_name_in_1c, repository))

    assert organization.name == "Образец"
    assert organization.name_in_1c == "ООО «Образец»"
    repository.name_in_1c_exists.assert_not_awaited()
    repository.save.assert_not_awaited()


def test_rename_organization_rejects_missing_organization(repository: MagicMock) -> None:
    organization_id = uuid4()
    repository.get.return_value = None

    with pytest.raises(OrganizationNotFoundError) as caught:
        asyncio.run(rename_organization(organization_id, "Пример", "ООО «Пример»", repository))

    assert caught.value.organization_id == organization_id
    repository.get.assert_awaited_once_with(organization_id)
    repository.name_exists.assert_not_awaited()
    repository.name_in_1c_exists.assert_not_awaited()
    repository.save.assert_not_awaited()
