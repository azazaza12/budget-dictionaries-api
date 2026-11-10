from collections.abc import Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from sigma.modules.dictionaries.facade import (
    DictionariesFacade,
    DuplicateDictionaryNameError,
    DuplicateOrganizationNameIn1CError,
    InvalidDictionaryNameError,
    OrganizationNotFoundError,
)
from sigma.modules.dictionaries.presentation.dependencies import (
    get_dictionaries_facade,
    require_dictionaries_admin,
)
from sigma.modules.dictionaries.routes import register


@dataclass(slots=True)
class OrganizationApi:
    client: TestClient
    dictionaries: MagicMock
    admin_check: MagicMock


@pytest.fixture
def organization_api() -> Iterator[OrganizationApi]:
    dictionaries = MagicMock(spec=DictionariesFacade)
    admin_check = MagicMock()

    def check_admin() -> None:
        admin_check()

    app = FastAPI()
    register(app)
    app.dependency_overrides[get_dictionaries_facade] = lambda: dictionaries
    app.dependency_overrides[require_dictionaries_admin] = check_admin

    with TestClient(app) as client:
        yield OrganizationApi(client, dictionaries, admin_check)


def test_create_organization_returns_created_organization(
    organization_api: OrganizationApi,
) -> None:
    organization = SimpleNamespace(
        id=uuid4(), name="Пример", name_in_1c="ООО «Тестовая Компания»", is_archived=False
    )
    organization_api.dictionaries.create_organization = AsyncMock(return_value=organization)

    response = organization_api.client.post(
        "/dictionaries/organizations",
        json={"name": "Пример", "name_in_1c": "ООО «Тестовая Компания»"},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": str(organization.id),
        "name": "Пример",
        "name_in_1c": "ООО «Тестовая Компания»",
        "is_archived": False,
    }
    organization_api.dictionaries.create_organization.assert_awaited_once_with(
        "Пример", "ООО «Тестовая Компания»"
    )
    organization_api.admin_check.assert_called_once_with()


def test_list_organizations_excludes_archived_by_default(organization_api: OrganizationApi) -> None:
    organization = SimpleNamespace(
        id=uuid4(), name="Пример", name_in_1c="ООО «Тестовая Компания»", is_archived=False
    )
    organization_api.dictionaries.list_organizations = AsyncMock(return_value=[organization])

    response = organization_api.client.get("/dictionaries/organizations")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(organization.id),
            "name": "Пример",
            "name_in_1c": "ООО «Тестовая Компания»",
            "is_archived": False,
        }
    ]
    organization_api.dictionaries.list_organizations.assert_awaited_once_with(
        include_archived=False
    )
    organization_api.admin_check.assert_not_called()


@pytest.mark.parametrize("include_archived", [False, True])
def test_list_organizations_forwards_query_filter(
    include_archived: bool, organization_api: OrganizationApi
) -> None:
    organization = SimpleNamespace(
        id=uuid4(),
        name="Пример",
        name_in_1c="ООО «Тестовая Компания»",
        is_archived=include_archived,
    )
    organization_api.dictionaries.list_organizations = AsyncMock(return_value=[organization])

    response = organization_api.client.get(
        "/dictionaries/organizations", params={"include_archived": str(include_archived).lower()}
    )

    assert response.status_code == 200
    assert response.json()[0]["is_archived"] is include_archived
    organization_api.dictionaries.list_organizations.assert_awaited_once_with(
        include_archived=include_archived
    )
    organization_api.admin_check.assert_not_called()


def test_list_organizations_returns_empty_list(organization_api: OrganizationApi) -> None:
    organization_api.dictionaries.list_organizations = AsyncMock(return_value=[])

    response = organization_api.client.get("/dictionaries/organizations")

    assert response.status_code == 200
    assert response.json() == []
    organization_api.dictionaries.list_organizations.assert_awaited_once_with(
        include_archived=False
    )


def test_invalid_organization_archive_filter_does_not_call_facade(
    organization_api: OrganizationApi,
) -> None:
    operation = AsyncMock()
    organization_api.dictionaries.list_organizations = operation

    response = organization_api.client.get(
        "/dictionaries/organizations", params={"include_archived": "invalid"}
    )

    assert response.status_code == 422
    operation.assert_not_awaited()


@pytest.mark.parametrize(("action", "is_archived"), [("archive", True), ("restore", False)])
def test_change_organization_archive_state(
    action: str, is_archived: bool, organization_api: OrganizationApi
) -> None:
    organization = SimpleNamespace(
        id=uuid4(),
        name="Пример",
        name_in_1c="ООО «Тестовая Компания»",
        is_archived=is_archived,
    )
    operation = AsyncMock(return_value=organization)
    setattr(organization_api.dictionaries, f"{action}_organization", operation)

    response = organization_api.client.post(
        f"/dictionaries/organizations/{organization.id}/{action}"
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": str(organization.id),
        "name": "Пример",
        "name_in_1c": "ООО «Тестовая Компания»",
        "is_archived": is_archived,
    }
    operation.assert_awaited_once_with(organization.id)
    organization_api.admin_check.assert_called_once_with()


@pytest.mark.parametrize("action", ["archive", "restore"])
def test_missing_organization_returns_404(action: str, organization_api: OrganizationApi) -> None:
    organization_id = uuid4()
    operation = AsyncMock(side_effect=OrganizationNotFoundError(organization_id))
    setattr(organization_api.dictionaries, f"{action}_organization", operation)

    response = organization_api.client.post(
        f"/dictionaries/organizations/{organization_id}/{action}"
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "organization_not_found",
        "context": {"organization_id": str(organization_id)},
    }
    operation.assert_awaited_once_with(organization_id)


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code", "expected_context"),
    [
        (
            DuplicateDictionaryNameError("Пример"),
            409,
            "duplicate_dictionary_name",
            {"name": "Пример"},
        ),
        (
            DuplicateOrganizationNameIn1CError("ООО «Тестовая Компания»"),
            409,
            "duplicate_organization_name_in_1c",
            {"name_in_1c": "ООО «Тестовая Компания»"},
        ),
        (InvalidDictionaryNameError("Empty name"), 422, "invalid_dictionary_name", {}),
    ],
)
def test_organization_name_errors(
    error: Exception,
    expected_status: int,
    expected_code: str,
    expected_context: dict[str, str],
    organization_api: OrganizationApi,
) -> None:
    operation = AsyncMock(side_effect=error)
    organization_api.dictionaries.create_organization = operation

    response = organization_api.client.post(
        "/dictionaries/organizations",
        json={"name": "Пример", "name_in_1c": "ООО «Тестовая Компания»"},
    )

    assert response.status_code == expected_status
    assert response.json() == {"code": expected_code, "context": expected_context}
    operation.assert_awaited_once_with("Пример", "ООО «Тестовая Компания»")


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"name": "Пример"},
        {"name_in_1c": "ООО «Тестовая Компания»"},
        {"name": None, "name_in_1c": "ООО «Тестовая Компания»"},
        {"name": "Пример", "name_in_1c": None},
        {"name": "Пример", "name_in_1c": "ООО «Тестовая Компания»", "is_archived": True},
    ],
)
def test_invalid_organization_input_does_not_call_facade(
    data: dict[str, object], organization_api: OrganizationApi
) -> None:
    operation = AsyncMock()
    organization_api.dictionaries.create_organization = operation

    response = organization_api.client.post("/dictionaries/organizations", json=data)

    assert response.status_code == 422
    operation.assert_not_awaited()


@pytest.mark.parametrize("action", ["archive", "restore"])
def test_invalid_organization_id_does_not_call_facade(
    action: str, organization_api: OrganizationApi
) -> None:
    operation = AsyncMock()
    setattr(organization_api.dictionaries, f"{action}_organization", operation)

    response = organization_api.client.post(f"/dictionaries/organizations/not-a-uuid/{action}")

    assert response.status_code == 422
    operation.assert_not_awaited()


@pytest.mark.parametrize(
    ("suffix", "operation_name"),
    [
        ("", "create_organization"),
        ("/{id}/archive", "archive_organization"),
        ("/{id}/restore", "restore_organization"),
    ],
)
def test_organization_writes_respect_admin_dependency(
    suffix: str, operation_name: str, organization_api: OrganizationApi
) -> None:
    organization_api.admin_check.side_effect = HTTPException(status_code=403, detail="Forbidden")
    operation = AsyncMock()
    setattr(organization_api.dictionaries, operation_name, operation)

    response = organization_api.client.post(
        f"/dictionaries/organizations{suffix.format(id=uuid4())}",
        json={"name": "Пример", "name_in_1c": "ООО «Тестовая Компания»"},
    )

    assert response.status_code == 403
    operation.assert_not_awaited()
    organization_api.admin_check.assert_called_once_with()
