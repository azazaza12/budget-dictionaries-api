from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import (
    CFO,
    MRP,
    ArchivedCategoryError,
    ArticleCategoryMismatchError,
    BudgetArticle,
    Category,
    DictionariesDomainError,
    InvalidDictionaryNameError,
    Organization,
    clean_name,
    normalize_1c_name,
    normalize_name,
)


def test_cfo_can_be_renamed_archived_and_restored() -> None:
    cfo = CFO(name="  Отдел   закупок ")

    assert cfo.name == "Отдел закупок"
    assert cfo.normalized_name == "отдел закупок"

    cfo.rename("  Отдел   снабжения ")
    cfo.archive()

    assert cfo.name == "Отдел снабжения"
    assert cfo.normalized_name == "отдел снабжения"
    assert cfo.is_archived

    cfo.restore()

    assert not cfo.is_archived


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
    assert error_type.code == expected_code


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

    with pytest.raises(ArchivedCategoryError) as error:
        BudgetArticle.create("Авиабилеты", category)

    assert error.value.category_id == category.id


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
    provided_category = Category(name="Командировки", id=uuid4())

    with pytest.raises(ArticleCategoryMismatchError) as error:
        article.restore(provided_category)

    assert article.is_archived
    assert error.value.article_id == article.id
    assert error.value.expected_category_id == category.id
    assert error.value.provided_category_id == provided_category.id


def test_mrp_cleans_name_and_exposes_normalized_name() -> None:
    mrp = MRP(name="  Иванов   ИВАН\tИванович ")

    assert mrp.name == "Иванов ИВАН Иванович"
    assert mrp.normalized_name == "иванов иван иванович"
    assert not mrp.is_archived


def test_mrp_generates_independent_ids() -> None:
    first = MRP(name="Иванов")
    second = MRP(name="Петров")

    assert first.id != second.id


def test_mrp_preserves_provided_id_and_archive_state() -> None:
    mrp_id = uuid4()

    mrp = MRP(id=mrp_id, name="Иванов", is_archived=True)

    assert mrp.id == mrp_id
    assert mrp.is_archived


def test_mrp_can_be_renamed() -> None:
    mrp = MRP(name="Иванов")

    mrp.rename("  ПЕТРОВ   Пётр ")

    assert mrp.name == "ПЕТРОВ Пётр"
    assert mrp.normalized_name == "петров пётр"


@pytest.mark.parametrize("name", ["", " \t\n "])
def test_mrp_rejects_empty_name(name: str) -> None:
    with pytest.raises(InvalidDictionaryNameError):
        MRP(name=name)


def test_mrp_rejects_empty_rename_without_mutation() -> None:
    mrp = MRP(name="Иванов")

    with pytest.raises(InvalidDictionaryNameError):
        mrp.rename(" \t ")

    assert mrp.name == "Иванов"


def test_mrp_archive_and_restore_are_idempotent() -> None:
    mrp = MRP(name="Иванов")
    original_id = mrp.id

    mrp.archive()
    mrp.archive()

    assert mrp.is_archived

    mrp.restore()
    mrp.restore()

    assert not mrp.is_archived
    assert mrp.id == original_id
    assert mrp.name == "Иванов"


@pytest.mark.parametrize(
    "name_in_1c",
    [
        'ООО "Тестовая Компания"',
        "ООО «Тестовая Компания»",
        "ООО “Тестовая Компания”",
        "ООО „Тестовая Компания“",
        "  оОо\t«Тестовая\u00a0\u00a0Компания»\n",
    ],
)
def test_normalize_1c_name_ignores_case_whitespace_and_quote_style(name_in_1c: str) -> None:
    assert normalize_1c_name(name_in_1c) == 'ооо "тестовая компания"'


@pytest.mark.parametrize("name_in_1c", ["", " \t\n ", "\u00a0"])
def test_normalize_1c_name_rejects_empty_value(name_in_1c: str) -> None:
    with pytest.raises(InvalidDictionaryNameError):
        normalize_1c_name(name_in_1c)


def test_normalize_1c_name_preserves_legal_form_and_punctuation() -> None:
    assert normalize_1c_name("ООО «Тестовая-Компания»") == 'ооо "тестовая-компания"'


def test_organization_cleans_fields_and_exposes_normalized_values() -> None:
    organization = Organization(
        name="  ПриМЕР\u00a0 ",
        name_in_1c="  ООО\t«Тестовая\u00a0\u00a0Компания»\n",
    )

    assert organization.normalized_name == "пример"
    assert organization.normalized_name_in_1c == 'ооо "тестовая компания"'
    assert organization.name == "ПриМЕР"
    assert organization.name_in_1c == "ООО «Тестовая Компания»"
    assert not organization.is_archived


@pytest.mark.parametrize("empty_value", ["", " \t\n ", "\u00a0"])
def test_organization_rejects_empty_name(empty_value: str) -> None:
    with pytest.raises(InvalidDictionaryNameError):
        Organization(name=empty_value, name_in_1c="ООО «Образец»")


@pytest.mark.parametrize("empty_value", ["", " \t\n ", "\u00a0"])
def test_organization_rejects_empty_name_in_1c(empty_value: str) -> None:
    with pytest.raises(InvalidDictionaryNameError):
        Organization(name="Образец", name_in_1c=empty_value)


@pytest.mark.parametrize("is_archived", [False, True])
def test_organization_archive_is_idempotent_and_preserves_identity(is_archived: bool) -> None:
    organization_id = uuid4()
    organization = Organization(
        id=organization_id,
        name="Образец",
        name_in_1c="ООО «Образец»",
        is_archived=is_archived,
    )

    organization.archive()
    organization.archive()

    assert organization.is_archived
    assert organization.id == organization_id
    assert organization.name == "Образец"
    assert organization.name_in_1c == "ООО «Образец»"


@pytest.mark.parametrize("is_archived", [False, True])
def test_organization_restore_is_idempotent_and_preserves_identity(is_archived: bool) -> None:
    organization_id = uuid4()
    organization = Organization(
        id=organization_id,
        name="Образец",
        name_in_1c="ООО «Образец»",
        is_archived=is_archived,
    )

    organization.restore()
    organization.restore()

    assert not organization.is_archived
    assert organization.id == organization_id
    assert organization.name == "Образец"
    assert organization.name_in_1c == "ООО «Образец»"


@pytest.mark.parametrize("is_archived", [False, True])
def test_organization_rename_changes_only_internal_name(is_archived: bool) -> None:
    organization = Organization(name="Образец", name_in_1c="ООО «Образец»", is_archived=is_archived)
    original_id = organization.id

    organization.rename("  ПриМЕР\u00a0 ")

    assert organization.name == "ПриМЕР"
    assert organization.normalized_name == "пример"
    assert organization.name_in_1c == "ООО «Образец»"
    assert organization.id == original_id
    assert organization.is_archived is is_archived


@pytest.mark.parametrize("is_archived", [False, True])
def test_organization_rename_in_1c_changes_only_1c_name(is_archived: bool) -> None:
    organization = Organization(name="Образец", name_in_1c="ООО «Образец»", is_archived=is_archived)
    original_id = organization.id

    organization.rename_in_1c("  ООО\t«Тестовая-Компания»\u00a0 ")

    assert organization.name == "Образец"
    assert organization.name_in_1c == "ООО «Тестовая-Компания»"
    assert organization.normalized_name_in_1c == 'ооо "тестовая-компания"'
    assert organization.id == original_id
    assert organization.is_archived is is_archived


@pytest.mark.parametrize("rename_in_1c", [False, True])
@pytest.mark.parametrize("empty_value", ["", " \t\n ", "\u00a0"])
def test_organization_rename_rejects_empty_values_without_mutation(
    rename_in_1c: bool, empty_value: str
) -> None:
    organization = Organization(name="Образец", name_in_1c="ООО «Образец»", is_archived=True)
    original_id = organization.id

    with pytest.raises(InvalidDictionaryNameError):
        if rename_in_1c:
            organization.rename_in_1c(empty_value)
        else:
            organization.rename(empty_value)

    assert organization.name == "Образец"
    assert organization.name_in_1c == "ООО «Образец»"
    assert organization.id == original_id
    assert organization.is_archived
