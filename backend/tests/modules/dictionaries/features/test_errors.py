from uuid import uuid4

import pytest

from sigma.modules.dictionaries.features.errors import (
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
    DictionariesFeatureError,
    DuplicateDictionaryNameError,
    DuplicateOrganizationNameIn1CError,
    MRPNotFoundError,
    OrganizationNotFoundError,
)


@pytest.mark.parametrize(
    ("error_type", "expected_code"),
    [
        (DuplicateDictionaryNameError, "duplicate_dictionary_name"),
        (CategoryNotFoundError, "category_not_found"),
        (BudgetArticleNotFoundError, "budget_article_not_found"),
        (MRPNotFoundError, "mrp_not_found"),
        (DuplicateOrganizationNameIn1CError, "duplicate_organization_name_in_1c"),
        (OrganizationNotFoundError, "organization_not_found"),
    ],
)
def test_feature_errors_have_stable_codes(
    error_type: type[DictionariesFeatureError],
    expected_code: str,
) -> None:
    assert error_type.code == expected_code


def test_duplicate_name_error_exposes_name() -> None:
    error = DuplicateDictionaryNameError("Авиабилеты")

    assert error.name == "Авиабилеты"


def test_duplicate_organization_1c_name_error_exposes_name_in_1c() -> None:
    error = DuplicateOrganizationNameIn1CError("ООО «Тестовая Компания»")

    assert error.name_in_1c == "ООО «Тестовая Компания»"
    assert error.name_in_1c in str(error)


def test_organization_not_found_error_exposes_organization_id() -> None:
    organization_id = uuid4()

    error = OrganizationNotFoundError(organization_id)

    assert error.organization_id == organization_id
    assert str(organization_id) in str(error)


def test_category_not_found_error_exposes_category_id() -> None:
    category_id = uuid4()

    error = CategoryNotFoundError(category_id)

    assert error.category_id == category_id


def test_budget_article_not_found_error_exposes_article_id() -> None:
    article_id = uuid4()

    error = BudgetArticleNotFoundError(article_id)

    assert error.article_id == article_id


def test_mrp_not_found_error_exposes_mrp_id() -> None:
    mrp_id = uuid4()

    error = MRPNotFoundError(mrp_id)

    assert error.mrp_id == mrp_id
