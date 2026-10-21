from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import (
    ArchivedCategoryError,
    ArticleCategoryMismatchError,
    BudgetArticle,
    Category,
    DictionariesDomainError,
    InvalidDictionaryNameError,
    clean_name,
    normalize_name,
)


@pytest.mark.parametrize(
    ("error_type", "expected_code"),
    [
        (InvalidDictionaryNameError, "invalid_dictionary_name"),
        (ArchivedCategoryError, "archived_category"),
        (ArticleCategoryMismatchError, "article_category_mismatch"),
    ],
)
def test_domain_errors_have_stable_codes(
    error_type: type[DictionariesDomainError],
    expected_code: str,
) -> None:
    assert error_type().code == expected_code


def test_clean_name_collapses_whitespace() -> None:
    assert clean_name("  Транспортные\t расходы ") == "Транспортные расходы"


def test_empty_name_is_rejected() -> None:
    with pytest.raises(InvalidDictionaryNameError):
        clean_name(" \t\n ")


def test_normalize_name_ignores_case_and_whitespace() -> None:
    assert normalize_name("  ТрансПОРТНЫЕ   расходы ") == "транспортные расходы"


def test_category_cleans_name_and_exposes_normalized_name() -> None:
    category = Category(name="  ТрансПОРТ  ")

    assert category.name == "ТрансПОРТ"
    assert category.normalized_name == "транспорт"
    assert not category.is_archived


def test_category_can_be_renamed_archived_and_restored() -> None:
    category = Category(name="Транспорт")

    category.rename("  Командировочные   расходы ")
    category.archive()

    assert category.name == "Командировочные расходы"
    assert category.normalized_name == "командировочные расходы"
    assert category.is_archived

    category.restore()

    assert not category.is_archived


def test_article_can_be_created_in_active_category() -> None:
    category = Category(name="Транспорт")

    article = BudgetArticle.create("  АвиаБИЛЕТЫ ", category)

    assert article.name == "АвиаБИЛЕТЫ"
    assert article.normalized_name == "авиабилеты"
    assert article.category_id == category.id
    assert not article.is_archived


def test_article_cannot_be_created_in_archived_category() -> None:
    category = Category(name="Транспорт", is_archived=True)

    with pytest.raises(ArchivedCategoryError):
        BudgetArticle.create("Авиабилеты", category)


def test_article_can_move_to_active_category() -> None:
    source_category = Category(name="Транспорт")
    target_category = Category(name="Командировки")
    article = BudgetArticle.create("Авиабилеты", source_category)

    article.move_to(target_category)

    assert article.category_id == target_category.id


def test_article_cannot_move_to_archived_category() -> None:
    source_category = Category(name="Транспорт")
    target_category = Category(name="Командировки", is_archived=True)
    article = BudgetArticle.create("Авиабилеты", source_category)

    with pytest.raises(ArchivedCategoryError):
        article.move_to(target_category)

    assert article.category_id == source_category.id


def test_article_can_be_restored_in_active_current_category() -> None:
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Авиабилеты", category)
    article.archive()

    article.restore(category)

    assert not article.is_archived


def test_article_cannot_be_restored_in_archived_category() -> None:
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Авиабилеты", category)
    article.archive()
    category.archive()

    with pytest.raises(ArchivedCategoryError):
        article.restore(category)

    assert article.is_archived


def test_article_cannot_be_restored_with_another_category() -> None:
    category = Category(name="Транспорт")
    article = BudgetArticle.create("Авиабилеты", category)
    article.archive()

    with pytest.raises(ArticleCategoryMismatchError):
        article.restore(Category(name="Командировки", id=uuid4()))

    assert article.is_archived
