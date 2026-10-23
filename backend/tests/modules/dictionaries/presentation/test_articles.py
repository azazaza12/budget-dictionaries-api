from collections.abc import Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sigma.modules.dictionaries.facade import DictionariesFacade
from sigma.modules.dictionaries.presentation.articles import router
from sigma.modules.dictionaries.presentation.dependencies import (
    get_dictionaries_facade,
    require_dictionaries_admin,
)


@dataclass(slots=True)
class ArticleApi:
    client: TestClient
    dictionaries: MagicMock
    admin_check: MagicMock


@pytest.fixture
def article_api() -> Iterator[ArticleApi]:
    dictionaries = MagicMock(spec=DictionariesFacade)
    admin_check = MagicMock()

    def check_admin() -> None:
        admin_check()

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_dictionaries_facade] = lambda: dictionaries
    app.dependency_overrides[require_dictionaries_admin] = check_admin

    with TestClient(app) as client:
        yield ArticleApi(client, dictionaries, admin_check)


def article_view(
    *,
    article_id: UUID | None = None,
    name: str = "Такси",
    category_id: UUID | None = None,
    is_archived: bool = False,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=article_id or uuid4(),
        name=name,
        category_id=category_id or uuid4(),
        is_archived=is_archived,
    )


def test_list_articles_excludes_archived_by_default(article_api: ArticleApi) -> None:
    article = article_view()
    article_api.dictionaries.list_articles = AsyncMock(return_value=[article])

    response = article_api.client.get("/dictionaries/articles")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": str(article.id),
            "name": "Такси",
            "category_id": str(article.category_id),
            "is_archived": False,
        }
    ]
    article_api.dictionaries.list_articles.assert_awaited_once_with(include_archived=False)
    article_api.admin_check.assert_not_called()


def test_list_articles_can_include_archived(article_api: ArticleApi) -> None:
    article = article_view(is_archived=True)
    article_api.dictionaries.list_articles = AsyncMock(return_value=[article])

    response = article_api.client.get("/dictionaries/articles", params={"include_archived": "true"})

    assert response.status_code == 200
    assert response.json()[0]["is_archived"] is True
    article_api.dictionaries.list_articles.assert_awaited_once_with(include_archived=True)
    article_api.admin_check.assert_not_called()


def test_create_article_returns_created_article(article_api: ArticleApi) -> None:
    category_id = uuid4()
    article = article_view(category_id=category_id)
    article_api.dictionaries.create_article = AsyncMock(return_value=article)

    response = article_api.client.post(
        "/dictionaries/articles",
        json={"name": "Такси", "category_id": str(category_id)},
    )

    assert response.status_code == 201
    assert response.json() == {
        "id": str(article.id),
        "name": "Такси",
        "category_id": str(category_id),
        "is_archived": False,
    }
    article_api.dictionaries.create_article.assert_awaited_once_with("Такси", category_id)
    article_api.admin_check.assert_called_once_with()


def test_rename_article_returns_updated_article(article_api: ArticleApi) -> None:
    article_id = uuid4()
    article = article_view(article_id=article_id, name="Каршеринг")
    article_api.dictionaries.rename_article = AsyncMock(return_value=article)

    response = article_api.client.put(
        f"/dictionaries/articles/{article_id}",
        json={"name": "Каршеринг"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Каршеринг"
    article_api.dictionaries.rename_article.assert_awaited_once_with(article_id, "Каршеринг")
    article_api.admin_check.assert_called_once_with()


def test_move_article_returns_article_in_target_category(article_api: ArticleApi) -> None:
    article_id = uuid4()
    target_category_id = uuid4()
    article = article_view(
        article_id=article_id,
        category_id=target_category_id,
    )
    article_api.dictionaries.move_article = AsyncMock(return_value=article)

    response = article_api.client.put(
        f"/dictionaries/articles/{article_id}/category",
        json={"category_id": str(target_category_id)},
    )

    assert response.status_code == 200
    assert response.json()["category_id"] == str(target_category_id)
    article_api.dictionaries.move_article.assert_awaited_once_with(article_id, target_category_id)
    article_api.admin_check.assert_called_once_with()


@pytest.mark.parametrize(
    ("action", "is_archived"),
    [("archive", True), ("restore", False)],
)
def test_change_article_archive_state(
    action: str,
    is_archived: bool,
    article_api: ArticleApi,
) -> None:
    article_id = uuid4()
    article = article_view(article_id=article_id, is_archived=is_archived)
    operation = AsyncMock(return_value=article)
    setattr(article_api.dictionaries, f"{action}_article", operation)

    response = article_api.client.post(f"/dictionaries/articles/{article_id}/{action}")

    assert response.status_code == 200
    assert response.json()["is_archived"] is is_archived
    operation.assert_awaited_once_with(article_id)
    article_api.admin_check.assert_called_once_with()
