from collections.abc import Iterator
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from sigma.main import create_app
from sigma.modules.dictionaries.facade import (
    ArchivedCategoryError,
    CategoryNotFoundError,
    DictionariesFacade,
    InvalidDictionaryNameError,
)
from sigma.modules.dictionaries.presentation.dependencies import get_dictionaries_facade


@dataclass(slots=True)
class DictionariesApi:
    client: TestClient
    dictionaries: MagicMock


@pytest.fixture
def dictionaries_api() -> Iterator[DictionariesApi]:
    app = create_app()
    dictionaries = MagicMock(spec=DictionariesFacade)
    app.dependency_overrides[get_dictionaries_facade] = lambda: dictionaries

    with TestClient(app) as client:
        yield DictionariesApi(client, dictionaries)


def test_application_exposes_all_dictionary_routes(dictionaries_api: DictionariesApi) -> None:
    response = dictionaries_api.client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    expected_routes = {
        "/dictionaries/categories": {"get", "post"},
        "/dictionaries/categories/{category_id}": {"put"},
        "/dictionaries/categories/{category_id}/archive": {"post"},
        "/dictionaries/categories/{category_id}/restore": {"post"},
        "/dictionaries/articles": {"get", "post"},
        "/dictionaries/articles/{article_id}": {"put"},
        "/dictionaries/articles/{article_id}/category": {"put"},
        "/dictionaries/articles/{article_id}/archive": {"post"},
        "/dictionaries/articles/{article_id}/restore": {"post"},
        "/dictionaries/mrps": {"get", "post"},
        "/dictionaries/mrps/{mrp_id}": {"put"},
        "/dictionaries/mrps/{mrp_id}/archive": {"post"},
        "/dictionaries/mrps/{mrp_id}/restore": {"post"},
    }
    for path, methods in expected_routes.items():
        assert set(paths[path]) == methods


@pytest.mark.parametrize("resource", ["categories", "articles", "mrps"])
def test_application_serves_dictionary_lists(
    resource: str,
    dictionaries_api: DictionariesApi,
) -> None:
    operation = AsyncMock(return_value=[])
    setattr(dictionaries_api.dictionaries, f"list_{resource}", operation)

    response = dictionaries_api.client.get(f"/dictionaries/{resource}")

    assert response.status_code == 200
    assert response.json() == []
    operation.assert_awaited_once_with(include_archived=False)


def test_application_handles_feature_errors(dictionaries_api: DictionariesApi) -> None:
    category_id = uuid4()
    dictionaries_api.dictionaries.rename_category = AsyncMock(
        side_effect=CategoryNotFoundError(category_id)
    )

    response = dictionaries_api.client.put(
        f"/dictionaries/categories/{category_id}", json={"name": "Транспорт"}
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "category_not_found",
        "context": {"category_id": str(category_id)},
    }


def test_application_handles_domain_errors(dictionaries_api: DictionariesApi) -> None:
    category_id = uuid4()
    dictionaries_api.dictionaries.create_article = AsyncMock(
        side_effect=ArchivedCategoryError(category_id)
    )

    response = dictionaries_api.client.post(
        "/dictionaries/articles",
        json={"name": "Такси", "category_id": str(category_id)},
    )

    assert response.status_code == 409
    assert response.json() == {
        "code": "archived_category",
        "context": {"category_id": str(category_id)},
    }


def test_application_handles_invalid_names(dictionaries_api: DictionariesApi) -> None:
    dictionaries_api.dictionaries.create_category = AsyncMock(
        side_effect=InvalidDictionaryNameError("Dictionary name must not be empty")
    )

    response = dictionaries_api.client.post("/dictionaries/categories", json={"name": " "})

    assert response.status_code == 422
    assert response.json() == {"code": "invalid_dictionary_name", "context": {}}
