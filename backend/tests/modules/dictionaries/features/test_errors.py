from uuid import uuid4

import pytest

from sigma.modules.dictionaries.features.errors import (
    CategoryNotFoundError,
    DictionariesFeatureError,
    DuplicateDictionaryNameError,
)


@pytest.mark.parametrize(
    ("error_type", "expected_code"),
    [
        (DuplicateDictionaryNameError, "duplicate_dictionary_name"),
        (CategoryNotFoundError, "category_not_found"),
    ],
)
def test_feature_errors_have_stable_codes(
    error_type: type[DictionariesFeatureError],
    expected_code: str,
) -> None:
    assert error_type.code == expected_code


def test_duplicate_name_error_exposes_name() -> None:
    error = DuplicateDictionaryNameError("Транспорт")

    assert error.name == "Транспорт"


def test_category_not_found_error_exposes_category_id() -> None:
    category_id = uuid4()

    error = CategoryNotFoundError(category_id)

    assert error.category_id == category_id
