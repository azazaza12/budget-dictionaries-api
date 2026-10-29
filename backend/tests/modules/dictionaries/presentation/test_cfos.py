from collections.abc import Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from sigma.modules.dictionaries.facade import (
    CFONotFoundError,
    DictionariesFacade,
    DuplicateDictionaryNameError,
    InvalidDictionaryNameError,
)
from sigma.modules.dictionaries.presentation.dependencies import (
    get_dictionaries_facade,
    require_dictionaries_admin,
)
from sigma.modules.dictionaries.routes import register


@dataclass(slots=True)
class CFOApi:
    client: TestClient
    dictionaries: MagicMock
    admin_check: MagicMock


@pytest.fixture
def cfo_api() -> Iterator[CFOApi]:
    dictionaries = MagicMock(spec=DictionariesFacade)
    admin_check = MagicMock()

    def check_admin() -> None:
        admin_check()

    app = FastAPI()
    register(app)
    app.dependency_overrides[get_dictionaries_facade] = lambda: dictionaries
    app.dependency_overrides[require_dictionaries_admin] = check_admin

    with TestClient(app) as client:
        yield CFOApi(client, dictionaries, admin_check)


def test_list_cfos_excludes_archived_by_default(cfo_api: CFOApi) -> None:
    cfo = SimpleNamespace(id=uuid4(), name="Закупки", is_archived=False)
    cfo_api.dictionaries.list_cfos = AsyncMock(return_value=[cfo])

    response = cfo_api.client.get("/dictionaries/cfos")

    assert response.status_code == 200
    assert response.json() == [{"id": str(cfo.id), "name": "Закупки", "is_archived": False}]
    cfo_api.dictionaries.list_cfos.assert_awaited_once_with(include_archived=False)
    cfo_api.admin_check.assert_not_called()


def test_list_cfos_can_include_archived(cfo_api: CFOApi) -> None:
    cfo = SimpleNamespace(id=uuid4(), name="Закупки", is_archived=True)
    cfo_api.dictionaries.list_cfos = AsyncMock(return_value=[cfo])

    response = cfo_api.client.get("/dictionaries/cfos", params={"include_archived": "true"})

    assert response.status_code == 200
    assert response.json()[0]["is_archived"] is True
    cfo_api.dictionaries.list_cfos.assert_awaited_once_with(include_archived=True)
    cfo_api.admin_check.assert_not_called()


def test_create_cfo_returns_created_cfo(cfo_api: CFOApi) -> None:
    cfo = SimpleNamespace(id=uuid4(), name="Закупки", is_archived=False)
    cfo_api.dictionaries.create_cfo = AsyncMock(return_value=cfo)

    response = cfo_api.client.post("/dictionaries/cfos", json={"name": "Закупки"})

    assert response.status_code == 201
    assert response.json() == {"id": str(cfo.id), "name": "Закупки", "is_archived": False}
    cfo_api.dictionaries.create_cfo.assert_awaited_once_with("Закупки")
    cfo_api.admin_check.assert_called_once_with()


def test_rename_cfo_returns_updated_cfo(cfo_api: CFOApi) -> None:
    cfo = SimpleNamespace(id=uuid4(), name="Снабжение", is_archived=False)
    cfo_api.dictionaries.rename_cfo = AsyncMock(return_value=cfo)

    response = cfo_api.client.put(f"/dictionaries/cfos/{cfo.id}", json={"name": "Снабжение"})

    assert response.status_code == 200
    assert response.json()["name"] == "Снабжение"
    cfo_api.dictionaries.rename_cfo.assert_awaited_once_with(cfo.id, "Снабжение")
    cfo_api.admin_check.assert_called_once_with()


@pytest.mark.parametrize(("action", "is_archived"), [("archive", True), ("restore", False)])
def test_change_cfo_archive_state(action: str, is_archived: bool, cfo_api: CFOApi) -> None:
    cfo = SimpleNamespace(id=uuid4(), name="Закупки", is_archived=is_archived)
    operation = AsyncMock(return_value=cfo)
    setattr(cfo_api.dictionaries, f"{action}_cfo", operation)

    response = cfo_api.client.post(f"/dictionaries/cfos/{cfo.id}/{action}")

    assert response.status_code == 200
    assert response.json()["is_archived"] is is_archived
    operation.assert_awaited_once_with(cfo.id)
    cfo_api.admin_check.assert_called_once_with()


@pytest.mark.parametrize(
    ("method", "suffix", "operation_name"),
    [
        ("put", "", "rename_cfo"),
        ("post", "/archive", "archive_cfo"),
        ("post", "/restore", "restore_cfo"),
    ],
)
def test_missing_cfo_returns_404(
    method: str, suffix: str, operation_name: str, cfo_api: CFOApi
) -> None:
    cfo_id = uuid4()
    operation = AsyncMock(side_effect=CFONotFoundError(cfo_id))
    setattr(cfo_api.dictionaries, operation_name, operation)

    response = cfo_api.client.request(
        method, f"/dictionaries/cfos/{cfo_id}{suffix}", json={"name": "Закупки"}
    )

    assert response.status_code == 404
    assert response.json() == {"code": "cfo_not_found", "context": {"cfo_id": str(cfo_id)}}


@pytest.mark.parametrize("rename", [False, True])
@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code", "expected_context"),
    [
        (
            DuplicateDictionaryNameError("Закупки"),
            409,
            "duplicate_dictionary_name",
            {"name": "Закупки"},
        ),
        (InvalidDictionaryNameError("Empty name"), 422, "invalid_dictionary_name", {}),
    ],
)
def test_cfo_name_errors(
    *,
    rename: bool,
    error: Exception,
    expected_status: int,
    expected_code: str,
    expected_context: dict[str, str],
    cfo_api: CFOApi,
) -> None:
    operation = AsyncMock(side_effect=error)
    operation_name = "rename_cfo" if rename else "create_cfo"
    setattr(cfo_api.dictionaries, operation_name, operation)
    path = f"/dictionaries/cfos/{uuid4()}" if rename else "/dictionaries/cfos"

    response = cfo_api.client.request("put" if rename else "post", path, json={"name": "Закупки"})

    assert response.status_code == expected_status
    assert response.json() == {"code": expected_code, "context": expected_context}


@pytest.mark.parametrize("rename", [False, True])
@pytest.mark.parametrize("data", [{}, {"name": None}, {"name": "Закупки", "is_archived": True}])
def test_invalid_cfo_input_does_not_call_facade(
    rename: bool, data: dict[str, object], cfo_api: CFOApi
) -> None:
    operation = AsyncMock()
    operation_name = "rename_cfo" if rename else "create_cfo"
    setattr(cfo_api.dictionaries, operation_name, operation)
    path = f"/dictionaries/cfos/{uuid4()}" if rename else "/dictionaries/cfos"

    response = cfo_api.client.request("put" if rename else "post", path, json=data)

    assert response.status_code == 422
    operation.assert_not_awaited()


@pytest.mark.parametrize(
    ("method", "suffix", "operation_name"),
    [
        ("post", "", "create_cfo"),
        ("put", "/{id}", "rename_cfo"),
        ("post", "/{id}/archive", "archive_cfo"),
        ("post", "/{id}/restore", "restore_cfo"),
    ],
)
def test_cfo_writes_respect_admin_dependency(
    method: str, suffix: str, operation_name: str, cfo_api: CFOApi
) -> None:
    cfo_api.admin_check.side_effect = HTTPException(status_code=403, detail="Forbidden")
    operation = AsyncMock()
    setattr(cfo_api.dictionaries, operation_name, operation)

    response = cfo_api.client.request(
        method,
        f"/dictionaries/cfos{suffix.format(id=uuid4())}",
        json={"name": "Закупки"},
    )

    assert response.status_code == 403
    operation.assert_not_awaited()


@pytest.mark.parametrize(
    ("method", "suffix", "operation_name"),
    [
        ("put", "", "rename_cfo"),
        ("post", "/archive", "archive_cfo"),
        ("post", "/restore", "restore_cfo"),
    ],
)
def test_invalid_cfo_id_does_not_call_facade(
    method: str, suffix: str, operation_name: str, cfo_api: CFOApi
) -> None:
    operation = AsyncMock()
    setattr(cfo_api.dictionaries, operation_name, operation)

    response = cfo_api.client.request(
        method, f"/dictionaries/cfos/not-a-uuid{suffix}", json={"name": "Закупки"}
    )

    assert response.status_code == 422
    operation.assert_not_awaited()
