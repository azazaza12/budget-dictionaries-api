import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import InvalidDictionaryNameError, Organization
from sigma.modules.dictionaries.features.errors import (
    DuplicateDictionaryNameError,
    DuplicateOrganizationExternalNameError,
    OrganizationNotFoundError,
)
from sigma.modules.dictionaries.features.rename_organization import rename_organization
from sigma.modules.dictionaries.repository import OrganizationRepository


@pytest.fixture
def repository() -> MagicMock:
    repository = MagicMock(spec=OrganizationRepository)
    repository.get = AsyncMock()
    repository.name_exists = AsyncMock(return_value=False)
    repository.external_name_exists = AsyncMock(return_value=False)
    repository.save = AsyncMock()
    return repository


@pytest.mark.parametrize("is_archived", [False, True])
def test_rename_organization_saves_cleaned_names(is_archived: bool, repository: MagicMock) -> None:
    organization = Organization(
        name="Образец", external_name="ООО «Образец»", is_archived=is_archived
    )
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
    assert organization.external_name == "ООО «Тестовая Компания»"
    assert organization.is_archived is is_archived
    repository.get.assert_awaited_once_with(organization_id)
    repository.name_exists.assert_awaited_once_with("пример", exclude_id=organization_id)
    repository.external_name_exists.assert_awaited_once_with(
        'ооо "тестовая компания"', exclude_id=organization_id
    )
    repository.save.assert_awaited_once_with(organization)


@pytest.mark.parametrize(
    ("new_name", "new_external_name", "normalized_name", "normalized_external_name"),
    [
        ("Образец", "ООО «Образец»", "образец", 'ооо "образец"'),
        ("Пример", "ООО «Образец»", "пример", 'ооо "образец"'),
        ("Образец", "ООО «Пример»", "образец", 'ооо "пример"'),
        ("ОБРАЗЕЦ", 'ООО "Образец"', "образец", 'ооо "образец"'),
    ],
)
def test_rename_organization_excludes_self_for_both_names(
    new_name: str,
    new_external_name: str,
    normalized_name: str,
    normalized_external_name: str,
    repository: MagicMock,
) -> None:
    organization = Organization(name="Образец", external_name="ООО «Образец»")
    repository.get.return_value = organization

    result = asyncio.run(
        rename_organization(organization.id, new_name, new_external_name, repository)
    )

    assert result is organization
    assert organization.name == new_name
    assert organization.external_name == new_external_name
    repository.name_exists.assert_awaited_once_with(normalized_name, exclude_id=organization.id)
    repository.external_name_exists.assert_awaited_once_with(
        normalized_external_name, exclude_id=organization.id
    )
    repository.save.assert_awaited_once_with(organization)


@pytest.mark.parametrize("duplicate_external", [False, True])
def test_rename_organization_rejects_duplicates_without_mutation(
    duplicate_external: bool, repository: MagicMock
) -> None:
    organization = Organization(name="Образец", external_name="ООО «Образец»")
    repository.get.return_value = organization
    repository.name_exists.return_value = not duplicate_external
    repository.external_name_exists.return_value = duplicate_external
    error_type = (
        DuplicateOrganizationExternalNameError
        if duplicate_external
        else DuplicateDictionaryNameError
    )

    with pytest.raises(error_type) as caught:
        asyncio.run(rename_organization(organization.id, "Пример", "ООО «Пример»", repository))

    assert organization.name == "Образец"
    assert organization.external_name == "ООО «Образец»"
    repository.name_exists.assert_awaited_once_with("пример", exclude_id=organization.id)
    if duplicate_external:
        assert isinstance(caught.value, DuplicateOrganizationExternalNameError)
        assert caught.value.external_name == "ООО «Пример»"
        repository.external_name_exists.assert_awaited_once_with(
            'ооо "пример"', exclude_id=organization.id
        )
    else:
        assert isinstance(caught.value, DuplicateDictionaryNameError)
        assert caught.value.name == "Пример"
        repository.external_name_exists.assert_not_awaited()
    repository.save.assert_not_awaited()


@pytest.mark.parametrize("empty_external", [False, True])
def test_rename_organization_rejects_empty_names_without_mutation(
    empty_external: bool, repository: MagicMock
) -> None:
    organization = Organization(name="Образец", external_name="ООО «Образец»")
    repository.get.return_value = organization
    new_name = "Пример" if empty_external else " \t "
    new_external_name = " \t " if empty_external else "ООО «Пример»"

    with pytest.raises(InvalidDictionaryNameError):
        asyncio.run(rename_organization(organization.id, new_name, new_external_name, repository))

    assert organization.name == "Образец"
    assert organization.external_name == "ООО «Образец»"
    repository.external_name_exists.assert_not_awaited()
    repository.save.assert_not_awaited()


def test_rename_organization_rejects_missing_organization(repository: MagicMock) -> None:
    organization_id = uuid4()
    repository.get.return_value = None

    with pytest.raises(OrganizationNotFoundError) as caught:
        asyncio.run(rename_organization(organization_id, "Пример", "ООО «Пример»", repository))

    assert caught.value.organization_id == organization_id
    repository.get.assert_awaited_once_with(organization_id)
    repository.name_exists.assert_not_awaited()
    repository.external_name_exists.assert_not_awaited()
    repository.save.assert_not_awaited()
