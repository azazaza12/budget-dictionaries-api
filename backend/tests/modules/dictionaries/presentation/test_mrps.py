from collections.abc import Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from sigma.main import create_app
from sigma.modules.dictionaries.facade import (
    DictionariesFacade,
    DuplicateDictionaryNameError,
    InvalidDictionaryNameError,
    MRPNotFoundError,
)
from sigma.modules.dictionaries.presentation.dependencies import (
    get_dictionaries_facade,
    require_dictionaries_admin,
)


@dataclass(slots=True)
class MRPApi:
    client: TestClient
    dictionaries: MagicMock
    admin_check: MagicMock


@pytest.fixture
def mrp_api() -> Iterator[MRPApi]:
    dictionaries = MagicMock(spec=DictionariesFacade)
    admin_check = MagicMock()

    def check_admin() -> None:
        admin_check()

    app = create_app()
    app.dependency_overrides[get_dictionaries_facade] = lambda: dictionaries
    app.dependency_overrides[require_dictionaries_admin] = check_admin

    with TestClient(app) as client:
        yield MRPApi(client, dictionaries, admin_check)


@pytest.mark.parametrize("include_archived", [None, "true"])
def test_list_mrps_returns_views_and_passes_filter(
    include_archived: str | None, mrp_api: MRPApi
) -> None:
    mrp_id = uuid4()
    archived = include_archived is not None
    mrp = SimpleNamespace(id=mrp_id, name="Иванов", is_archived=archived, normalized_name="иванов")
    mrp_api.dictionaries.list_mrps = AsyncMock(return_value=[mrp])
    params = {} if include_archived is None else {"include_archived": include_archived}

    response = mrp_api.client.get("/dictionaries/mrps", params=params)

    assert response.status_code == 200
    assert response.json() == [{"id": str(mrp_id), "name": "Иванов", "is_archived": archived}]
    mrp_api.dictionaries.list_mrps.assert_awaited_once_with(include_archived=archived)
    mrp_api.admin_check.assert_not_called()


def test_create_mrp_returns_created_view(mrp_api: MRPApi) -> None:
    mrp_id = uuid4()
    mrp = SimpleNamespace(id=mrp_id, name="Иванов", is_archived=False)
    mrp_api.dictionaries.create_mrp = AsyncMock(return_value=mrp)

    response = mrp_api.client.post("/dictionaries/mrps", json={"name": "Иванов"})

    assert response.status_code == 201
    assert response.json() == {"id": str(mrp_id), "name": "Иванов", "is_archived": False}
    mrp_api.dictionaries.create_mrp.assert_awaited_once_with("Иванов")
    mrp_api.admin_check.assert_called_once_with()


def test_rename_mrp_returns_updated_view(mrp_api: MRPApi) -> None:
    mrp_id = uuid4()
    mrp = SimpleNamespace(id=mrp_id, name="Петров", is_archived=False)
    mrp_api.dictionaries.rename_mrp = AsyncMock(return_value=mrp)

    response = mrp_api.client.put(f"/dictionaries/mrps/{mrp_id}", json={"name": "Петров"})

    assert response.status_code == 200
    assert response.json() == {"id": str(mrp_id), "name": "Петров", "is_archived": False}
    mrp_api.dictionaries.rename_mrp.assert_awaited_once_with(mrp_id, "Петров")
    mrp_api.admin_check.assert_called_once_with()


@pytest.mark.parametrize(("action", "archived"), [("archive", True), ("restore", False)])
def test_change_mrp_archive_state(action: str, archived: bool, mrp_api: MRPApi) -> None:
    mrp_id = uuid4()
    operation = AsyncMock(
        return_value=SimpleNamespace(id=mrp_id, name="Иванов", is_archived=archived)
    )
    setattr(mrp_api.dictionaries, f"{action}_mrp", operation)

    response = mrp_api.client.post(f"/dictionaries/mrps/{mrp_id}/{action}")

    assert response.status_code == 200
    assert response.json() == {"id": str(mrp_id), "name": "Иванов", "is_archived": archived}
    operation.assert_awaited_once_with(mrp_id)
    mrp_api.admin_check.assert_called_once_with()


@pytest.mark.parametrize("action", ["rename", "archive", "restore"])
def test_mrp_writes_return_not_found(action: str, mrp_api: MRPApi) -> None:
    mrp_id = uuid4()
    operation = AsyncMock(side_effect=MRPNotFoundError(mrp_id))
    setattr(mrp_api.dictionaries, f"{action}_mrp", operation)

    if action == "rename":
        response = mrp_api.client.put(f"/dictionaries/mrps/{mrp_id}", json={"name": "Иванов"})
    else:
        response = mrp_api.client.post(f"/dictionaries/mrps/{mrp_id}/{action}")

    assert response.status_code == 404
    assert response.json() == {"code": "mrp_not_found", "context": {"mrp_id": str(mrp_id)}}


@pytest.mark.parametrize("rename", [False, True])
@pytest.mark.parametrize("duplicate", [False, True])
def test_mrp_name_errors_are_mapped(rename: bool, duplicate: bool, mrp_api: MRPApi) -> None:
    error = (
        DuplicateDictionaryNameError("Иванов")
        if duplicate
        else InvalidDictionaryNameError("Dictionary name must not be empty")
    )
    operation = AsyncMock(side_effect=error)
    if rename:
        mrp_api.dictionaries.rename_mrp = operation
        response = mrp_api.client.put(f"/dictionaries/mrps/{uuid4()}", json={"name": "Иванов"})
    else:
        mrp_api.dictionaries.create_mrp = operation
        response = mrp_api.client.post("/dictionaries/mrps", json={"name": "Иванов"})

    assert response.status_code == (409 if duplicate else 422)
    assert response.json() == {
        "code": "duplicate_dictionary_name" if duplicate else "invalid_dictionary_name",
        "context": {"name": "Иванов"} if duplicate else {},
    }


@pytest.mark.parametrize("rename", [False, True])
@pytest.mark.parametrize("body", [{}, {"name": None}, {"name": 42}, {"name": "Иванов", "id": "x"}])
def test_mrp_rejects_invalid_input(rename: bool, body: dict[str, object], mrp_api: MRPApi) -> None:
    if rename:
        response = mrp_api.client.put(f"/dictionaries/mrps/{uuid4()}", json=body)
    else:
        response = mrp_api.client.post("/dictionaries/mrps", json=body)

    assert response.status_code == 422
    mrp_api.dictionaries.create_mrp.assert_not_called()
    mrp_api.dictionaries.rename_mrp.assert_not_called()


@pytest.mark.parametrize("action", ["rename", "archive", "restore"])
def test_mrp_rejects_invalid_id(action: str, mrp_api: MRPApi) -> None:
    if action == "rename":
        response = mrp_api.client.put("/dictionaries/mrps/invalid", json={"name": "Иванов"})
    else:
        response = mrp_api.client.post(f"/dictionaries/mrps/invalid/{action}")

    assert response.status_code == 422
    mrp_api.dictionaries.rename_mrp.assert_not_called()
    mrp_api.dictionaries.archive_mrp.assert_not_called()
    mrp_api.dictionaries.restore_mrp.assert_not_called()


@pytest.mark.parametrize("action", ["create", "rename", "archive", "restore"])
def test_mrp_write_stops_when_admin_dependency_denies_access(action: str, mrp_api: MRPApi) -> None:
    mrp_api.admin_check.side_effect = HTTPException(status_code=403, detail="Forbidden")
    mrp_id = uuid4()

    if action == "create":
        response = mrp_api.client.post("/dictionaries/mrps", json={"name": "Иванов"})
    elif action == "rename":
        response = mrp_api.client.put(f"/dictionaries/mrps/{mrp_id}", json={"name": "Иванов"})
    else:
        response = mrp_api.client.post(f"/dictionaries/mrps/{mrp_id}/{action}")

    assert response.status_code == 403
    mrp_api.dictionaries.create_mrp.assert_not_called()
    mrp_api.dictionaries.rename_mrp.assert_not_called()
    mrp_api.dictionaries.archive_mrp.assert_not_called()
    mrp_api.dictionaries.restore_mrp.assert_not_called()
