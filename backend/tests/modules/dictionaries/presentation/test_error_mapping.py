from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from sigma.modules.dictionaries.facade import (
    ArchivedCategoryError,
    ArticleCategoryMismatchError,
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
    CFONotFoundError,
    DictionariesDomainError,
    DictionariesFeatureError,
    DuplicateDictionaryNameError,
    InvalidDictionaryNameError,
    MRPNotFoundError,
)
from sigma.modules.dictionaries.presentation.error_mapping import dictionaries_error

ARTICLE_ID = uuid4()
CATEGORY_ID = uuid4()
EXPECTED_CATEGORY_ID = uuid4()
PROVIDED_CATEGORY_ID = uuid4()
MRP_ID = uuid4()
CFO_ID = uuid4()


@pytest.mark.parametrize(
    ("error", "expected_status", "expected_code", "expected_context"),
    [
        (CFONotFoundError(CFO_ID), 404, "cfo_not_found", {"cfo_id": str(CFO_ID)}),
        (
            MRPNotFoundError(MRP_ID),
            404,
            "mrp_not_found",
            {"mrp_id": str(MRP_ID)},
        ),
        (
            CategoryNotFoundError(CATEGORY_ID),
            404,
            "category_not_found",
            {"category_id": str(CATEGORY_ID)},
        ),
        (
            BudgetArticleNotFoundError(ARTICLE_ID),
            404,
            "budget_article_not_found",
            {"article_id": str(ARTICLE_ID)},
        ),
        (
            DuplicateDictionaryNameError("Такси"),
            409,
            "duplicate_dictionary_name",
            {"name": "Такси"},
        ),
        (
            ArchivedCategoryError(CATEGORY_ID),
            409,
            "archived_category",
            {"category_id": str(CATEGORY_ID)},
        ),
        (
            ArticleCategoryMismatchError(
                ARTICLE_ID,
                EXPECTED_CATEGORY_ID,
                PROVIDED_CATEGORY_ID,
            ),
            409,
            "article_category_mismatch",
            {
                "article_id": str(ARTICLE_ID),
                "expected_category_id": str(EXPECTED_CATEGORY_ID),
                "provided_category_id": str(PROVIDED_CATEGORY_ID),
            },
        ),
        (
            InvalidDictionaryNameError("Dictionary name must not be empty"),
            422,
            "invalid_dictionary_name",
            {},
        ),
    ],
)
def test_dictionaries_error_mapping(
    error: Exception,
    expected_status: int,
    expected_code: str,
    expected_context: dict[str, str],
) -> None:
    app = FastAPI()
    app.add_exception_handler(DictionariesDomainError, dictionaries_error)
    app.add_exception_handler(DictionariesFeatureError, dictionaries_error)

    @app.get("/error")
    async def raise_error() -> None:
        raise error

    with TestClient(app) as client:
        response = client.get("/error")

    assert response.status_code == expected_status
    assert response.json() == {
        "code": expected_code,
        "context": expected_context,
    }
