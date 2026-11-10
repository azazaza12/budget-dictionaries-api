from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

from sigma.modules.dictionaries.domain import Organization
from sigma.modules.dictionaries.presentation.schemas import (
    BudgetArticleCategoryInput,
    BudgetArticleInput,
    BudgetArticleNameInput,
    BudgetArticleView,
    CategoryInput,
    CategoryView,
    CFOInput,
    CFOView,
    MRPInput,
    MRPView,
    OrganizationInput,
    OrganizationView,
)


def test_category_input_accepts_name() -> None:
    data = CategoryInput(name="Транспорт")

    assert data.name == "Транспорт"


def test_budget_article_input_parses_category_id() -> None:
    category_id = uuid4()

    data = BudgetArticleInput.model_validate(
        {"name": "Авиабилеты", "category_id": str(category_id)}
    )

    assert data.name == "Авиабилеты"
    assert data.category_id == category_id


def test_budget_article_name_input_accepts_name() -> None:
    data = BudgetArticleNameInput(name="Железнодорожные билеты")

    assert data.name == "Железнодорожные билеты"


def test_budget_article_category_input_parses_category_id() -> None:
    category_id = uuid4()

    data = BudgetArticleCategoryInput.model_validate({"category_id": str(category_id)})

    assert data.category_id == category_id


@pytest.mark.parametrize(
    ("schema", "data"),
    [
        (CFOInput, {"name": "Закупки"}),
        (CategoryInput, {"name": "Транспорт"}),
        (MRPInput, {"name": "Иванов"}),
        (BudgetArticleInput, {"name": "Авиабилеты", "category_id": uuid4()}),
        (BudgetArticleNameInput, {"name": "Авиабилеты"}),
        (BudgetArticleCategoryInput, {"category_id": uuid4()}),
        (OrganizationInput, {"name": "Пример", "name_in_1c": "ООО «Тестовая Компания»"}),
    ],
)
def test_input_schemas_reject_extra_fields(
    schema: type[BaseModel],
    data: dict[str, object],
) -> None:
    with pytest.raises(ValidationError):
        schema.model_validate({**data, "is_archived": True})


def test_category_view_reads_object_attributes() -> None:
    category_id = uuid4()
    category = SimpleNamespace(
        id=category_id,
        name="Транспорт",
        is_archived=False,
        normalized_name="транспорт",
    )

    view = CategoryView.model_validate(category)

    assert view.model_dump(mode="json") == {
        "id": str(category_id),
        "name": "Транспорт",
        "is_archived": False,
    }


def test_cfo_view_reads_attributes_without_exposing_normalized_name() -> None:
    cfo = SimpleNamespace(id=uuid4(), name="Закупки", is_archived=False, normalized_name="закупки")

    view = CFOView.model_validate(cfo)

    assert view.model_dump(mode="json") == {
        "id": str(cfo.id),
        "name": "Закупки",
        "is_archived": False,
    }


def test_budget_article_view_reads_object_attributes() -> None:
    article_id = uuid4()
    category_id = uuid4()
    article = SimpleNamespace(
        id=article_id,
        name="Авиабилеты",
        category_id=category_id,
        is_archived=True,
        normalized_name="авиабилеты",
    )

    view = BudgetArticleView.model_validate(article)

    assert view.model_dump(mode="json") == {
        "id": str(article_id),
        "name": "Авиабилеты",
        "category_id": str(category_id),
        "is_archived": True,
    }


def test_category_view_validates_list_items() -> None:
    categories = [
        SimpleNamespace(id=uuid4(), name="Транспорт", is_archived=False),
        SimpleNamespace(id=uuid4(), name="Командировки", is_archived=True),
    ]

    views = TypeAdapter(list[CategoryView]).validate_python(categories)

    assert [view.name for view in views] == ["Транспорт", "Командировки"]


def test_mrp_input_accepts_name() -> None:
    assert MRPInput(name="Иванов").name == "Иванов"


def test_mrp_view_reads_attributes_without_exposing_normalized_name() -> None:
    mrp_id = uuid4()
    mrp = SimpleNamespace(id=mrp_id, name="Иванов", is_archived=True, normalized_name="иванов")

    assert MRPView.model_validate(mrp).model_dump(mode="json") == {
        "id": str(mrp_id),
        "name": "Иванов",
        "is_archived": True,
    }


def test_organization_input_accepts_both_names() -> None:
    data = OrganizationInput(name="Пример", name_in_1c="ООО «Тестовая Компания»")

    assert data.name == "Пример"
    assert data.name_in_1c == "ООО «Тестовая Компания»"


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"name": "Пример"},
        {"name_in_1c": "ООО «Тестовая Компания»"},
        {"name": None, "name_in_1c": "ООО «Тестовая Компания»"},
        {"name": "Пример", "name_in_1c": None},
    ],
)
def test_organization_input_requires_both_names(data: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        OrganizationInput.model_validate(data)


@pytest.mark.parametrize("is_archived", [False, True])
def test_organization_view_reads_domain_without_exposing_normalized_names(
    is_archived: bool,
) -> None:
    organization = Organization(
        name="Пример", name_in_1c="ООО «Тестовая Компания»", is_archived=is_archived
    )

    view = OrganizationView.model_validate(organization)

    assert view.model_dump(mode="json") == {
        "id": str(organization.id),
        "name": "Пример",
        "name_in_1c": "ООО «Тестовая Компания»",
        "is_archived": is_archived,
    }
