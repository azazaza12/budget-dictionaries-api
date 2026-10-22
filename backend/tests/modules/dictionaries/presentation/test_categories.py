from collections.abc import Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sigma.modules.dictionaries.facade import DictionariesFacade
from sigma.modules.dictionaries.presentation.categories import router
from sigma.modules.dictionaries.presentation.dependencies import (
    get_dictionaries_facade,
    require_dictionaries_admin,
)


@dataclass(slots=True)
class CategoryApi:
    client: TestClient
    dictionaries: MagicMock
    admin_check: MagicMock


@pytest.fixture
def category_api() -> Iterator[CategoryApi]:
    dictionaries = MagicMock(spec=DictionariesFacade)
    admin_check = MagicMock()

    def check_admin() -> None:
        admin_check()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_dictionaries_facade] = lambda: dictionaries
    app.dependency_overrides[require_dictionaries_admin] = check_admin

    with TestClient(app) as client:
        yield CategoryApi(client, dictionaries, admin_check)


def category_view(
    *,
    category_id: UUID | None = None,
    name: str = "Транспорт",
    is_archived: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=category_id or uuid4(),
        name=name,
        is_archived=is_archived,
    )


def test_list_categories_excludes_archived_by_default(category_api: CategoryApi) -> None:
    category = category_view()
    category_api.dictionaries.list_categories = AsyncMock(return_value=[category])

    response = category_api.client.get("/dictionaries/categories")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(category.id),
            "name": "Транспорт",
            "is_archived": False,
        }
    ]
    category_api.dictionaries.list_categories.assert_awaited_once_with(include_archived=False)
    category_api.admin_check.assert_not_called()


def test_list_categories_can_include_archived(category_api: CategoryApi) -> None:
    category = category_view(is_archived=True)
    category_api.dictionaries.list_categories = AsyncMock(return_value=[category])

    response = category_api.client.get(
        "/dictionaries/categories", params={"include_archived": "true"}
    )

    assert response.status_code == 200
    assert response.json()[0]["is_archived"] is True
    category_api.dictionaries.list_categories.assert_awaited_once_with(include_archived=True)
    category_api.admin_check.assert_not_called()


def test_create_category_returns_created_category(category_api: CategoryApi) -> None:
    category = category_view()
    category_api.dictionaries.create_category = AsyncMock(return_value=category)

    response = category_api.client.post("/dictionaries/categories", json={"name": "Транспорт"})

    assert response.status_code == 201
    assert response.json() == {
        "id": str(category.id),
        "name": "Транспорт",
        "is_archived": False,
    }
    category_api.dictionaries.create_category.assert_awaited_once_with("Транспорт")
    category_api.admin_check.assert_called_once_with()


def test_rename_category_returns_updated_category(category_api: CategoryApi) -> None:
    category_id = uuid4()
    category = category_view(category_id=category_id, name="Командировки")
    category_api.dictionaries.rename_category = AsyncMock(return_value=category)

    response = category_api.client.put(
        f"/dictionaries/categories/{category_id}",
        json={"name": "Командировки"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Командировки"
    category_api.dictionaries.rename_category.assert_awaited_once_with(category_id, "Командировки")
    category_api.admin_check.assert_called_once_with()


@pytest.mark.parametrize(
    ("action", "is_archived"),
    [("archive", True), ("restore", False)],
)
def test_change_category_archive_state(
    action: str,
    is_archived: bool,
    category_api: CategoryApi,
) -> None:
    category_id = uuid4()
    category = category_view(category_id=category_id, is_archived=is_archived)
    operation = AsyncMock(return_value=category)
    setattr(category_api.dictionaries, f"{action}_category", operation)

    response = category_api.client.post(f"/dictionaries/categories/{category_id}/{action}")

    assert response.status_code == 200
    assert response.json()["is_archived"] is is_archived
    operation.assert_awaited_once_with(category_id)
    category_api.admin_check.assert_called_once_with()
