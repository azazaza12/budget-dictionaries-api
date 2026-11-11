from uuid import UUID, uuid4

import pytest

from sigma.modules.dictionaries.features.errors import (
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
    CFONotFoundError,
    DictionariesFeatureError,
    DistributionRuleNotFoundError,
    DuplicateDictionaryNameError,
    DuplicateDistributionRuleError,
    MRPNotFoundError,
)


@pytest.mark.parametrize(
    ("error_type", "expected_code"),
    [
        (DuplicateDictionaryNameError, "duplicate_dictionary_name"),
        (CategoryNotFoundError, "category_not_found"),
        (CFONotFoundError, "cfo_not_found"),
        (BudgetArticleNotFoundError, "budget_article_not_found"),
        (MRPNotFoundError, "mrp_not_found"),
        (DuplicateDistributionRuleError, "duplicate_savings_distribution_rule"),
        (DistributionRuleNotFoundError, "savings_distribution_rule_not_found"),
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


@pytest.mark.parametrize("use_keywords", [False, True])
@pytest.mark.parametrize(
    ("error_type", "field_name", "value"),
    [
        (DuplicateDictionaryNameError, "name", "Авиабилеты"),
        (CategoryNotFoundError, "category_id", uuid4()),
        (CFONotFoundError, "cfo_id", uuid4()),
        (BudgetArticleNotFoundError, "article_id", uuid4()),
        (MRPNotFoundError, "mrp_id", uuid4()),
        (DuplicateDistributionRuleError, "rule_id", uuid4()),
        (DistributionRuleNotFoundError, "rule_id", uuid4()),
    ],
)
def test_feature_errors_expose_explicit_fields(
    use_keywords: bool,
    error_type: type[DictionariesFeatureError],
    field_name: str,
    value: str | UUID,
) -> None:
    context = {field_name: value}

    error = error_type(**context) if use_keywords else error_type(value)

    assert vars(error) == context
    assert error != error_type(**context)
