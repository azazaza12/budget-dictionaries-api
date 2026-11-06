from collections.abc import Iterator
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from sigma.main import create_app
from sigma.modules.dictionaries.facade import (
    ArchivedBudgetArticleError,
    ArchivedCFOError,
    ArchivedMRPError,
    BudgetArticleNotFoundError,
    CFONotFoundError,
    DictionariesFacade,
    DuplicateSavingsDistributionRuleError,
    MRPNotFoundError,
    SavingsDistributionRuleNotFoundError,
)
from sigma.modules.dictionaries.presentation.dependencies import (
    get_dictionaries_facade,
    require_dictionaries_admin,
)


@dataclass(slots=True)
class DistributionRulesApi:
    client: TestClient
    dictionaries: MagicMock
    admin_check: MagicMock


@pytest.fixture
def rules_api() -> Iterator[DistributionRulesApi]:
    dictionaries = MagicMock(spec=DictionariesFacade)
    admin_check = MagicMock()

    def check_admin() -> None:
        admin_check()

    app = create_app()
    app.dependency_overrides[get_dictionaries_facade] = lambda: dictionaries
    app.dependency_overrides[require_dictionaries_admin] = check_admin

    with TestClient(app) as client:
        yield DistributionRulesApi(client, dictionaries, admin_check)


def test_recommendation_returns_mrp_view_without_admin_access(
    rules_api: DistributionRulesApi,
) -> None:
    rules_api.admin_check.side_effect = HTTPException(status_code=403, detail="Forbidden")
    cfo_id, article_id, mrp_id = uuid4(), uuid4(), uuid4()
    rules_api.dictionaries.find_mrp_by_savings_distribution_rule = AsyncMock(
        return_value=SimpleNamespace(
            id=mrp_id, name="Иванов", is_archived=False, normalized_name="иванов"
        )
    )

    response = rules_api.client.get(
        "/dictionaries/savings-distribution-rules/recommendation",
        params={"cfo_id": str(cfo_id), "budget_article_id": str(article_id)},
    )

    assert response.status_code == 200
    assert response.json() == {"id": str(mrp_id), "name": "Иванов", "is_archived": False}
    rules_api.dictionaries.find_mrp_by_savings_distribution_rule.assert_awaited_once_with(
        cfo_id, article_id
    )
    rules_api.admin_check.assert_not_called()


def test_recommendation_returns_null_when_no_match(rules_api: DistributionRulesApi) -> None:
    cfo_id, article_id = uuid4(), uuid4()
    rules_api.dictionaries.find_mrp_by_savings_distribution_rule = AsyncMock(return_value=None)

    response = rules_api.client.get(
        "/dictionaries/savings-distribution-rules/recommendation",
        params={"cfo_id": str(cfo_id), "budget_article_id": str(article_id)},
    )

    assert response.status_code == 200
    assert response.json() is None
    rules_api.dictionaries.find_mrp_by_savings_distribution_rule.assert_awaited_once_with(
        cfo_id, article_id
    )
    rules_api.admin_check.assert_not_called()


@pytest.mark.parametrize("parameter", ["cfo_id", "budget_article_id"])
@pytest.mark.parametrize("invalid_value", [None, "", "not-a-uuid"])
def test_recommendation_rejects_missing_or_invalid_query(
    parameter: str, invalid_value: str | None, rules_api: DistributionRulesApi
) -> None:
    params = {"cfo_id": str(uuid4()), "budget_article_id": str(uuid4())}
    if invalid_value is None:
        del params[parameter]
    else:
        params[parameter] = invalid_value

    response = rules_api.client.get(
        "/dictionaries/savings-distribution-rules/recommendation", params=params
    )

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", parameter]
    rules_api.dictionaries.find_mrp_by_savings_distribution_rule.assert_not_called()


def test_recommendation_openapi_describes_required_uuid_query_and_nullable_view(
    rules_api: DistributionRulesApi,
) -> None:
    response = rules_api.client.get("/openapi.json")

    assert response.status_code == 200
    operation = response.json()["paths"]["/dictionaries/savings-distribution-rules/recommendation"][
        "get"
    ]
    assert {parameter["name"] for parameter in operation["parameters"]} == {
        "cfo_id",
        "budget_article_id",
    }
    for parameter in operation["parameters"]:
        assert parameter["in"] == "query"
        assert parameter["required"] is True
        assert parameter["schema"]["format"] == "uuid"
    schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
    assert {"$ref": "#/components/schemas/MRPView"} in schema["anyOf"]
    assert {"type": "null"} in schema["anyOf"]


@pytest.fixture
def rule() -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), cfo_id=uuid4(), budget_article_id=uuid4(), mrp_id=uuid4())


def _rule_input(rule: SimpleNamespace) -> dict[str, str]:
    return {
        "cfo_id": str(rule.cfo_id),
        "budget_article_id": str(rule.budget_article_id),
        "mrp_id": str(rule.mrp_id),
    }


@pytest.mark.parametrize("update", [False, True])
def test_rule_write_returns_view(
    update: bool, rule: SimpleNamespace, rules_api: DistributionRulesApi
) -> None:
    operation = AsyncMock(return_value=rule)
    action = "update" if update else "create"
    setattr(rules_api.dictionaries, f"{action}_savings_distribution_rule", operation)
    path = "/dictionaries/savings-distribution-rules"

    response = rules_api.client.request(
        "PUT" if update else "POST",
        f"{path}/{rule.id}" if update else path,
        json=_rule_input(rule),
    )

    assert response.status_code == (200 if update else 201)
    assert response.json() == {"id": str(rule.id), **_rule_input(rule)}
    args = (rule.cfo_id, rule.budget_article_id, rule.mrp_id)
    operation.assert_awaited_once_with(*((rule.id, *args) if update else args))
    rules_api.admin_check.assert_called_once_with()


def test_get_rule_returns_view(rule: SimpleNamespace, rules_api: DistributionRulesApi) -> None:
    rules_api.dictionaries.get_savings_distribution_rule = AsyncMock(return_value=rule)

    response = rules_api.client.get(f"/dictionaries/savings-distribution-rules/{rule.id}")

    assert response.status_code == 200
    assert response.json() == {"id": str(rule.id), **_rule_input(rule)}
    rules_api.dictionaries.get_savings_distribution_rule.assert_awaited_once_with(rule.id)
    rules_api.admin_check.assert_not_called()


@pytest.mark.parametrize("archived", [False, True])
def test_list_rules_returns_nested_views(
    archived: bool, rule: SimpleNamespace, rules_api: DistributionRulesApi
) -> None:
    category_id = uuid4()
    cfo = {"id": str(rule.cfo_id), "name": "Закупки", "is_archived": archived}
    article = {
        "id": str(rule.budget_article_id),
        "name": "Билеты",
        "is_archived": archived,
        "category_id": str(category_id),
    }
    category = {"id": str(category_id), "name": "Командировки", "is_archived": archived}
    mrp = {"id": str(rule.mrp_id), "name": "Иванов", "is_archived": archived}
    item = SimpleNamespace(
        rule=rule,
        cfo=SimpleNamespace(**cfo),
        budget_article=SimpleNamespace(**article),
        category=SimpleNamespace(**category),
        mrp=SimpleNamespace(**mrp),
    )
    rules_api.dictionaries.list_savings_distribution_rules = AsyncMock(return_value=[item])

    response = rules_api.client.get("/dictionaries/savings-distribution-rules")

    assert response.status_code == 200
    assert response.json() == [
        {
            "rule": {"id": str(rule.id), **_rule_input(rule)},
            "cfo": cfo,
            "budget_article": article,
            "category": category,
            "mrp": mrp,
        }
    ]
    rules_api.dictionaries.list_savings_distribution_rules.assert_awaited_once_with()
    rules_api.admin_check.assert_not_called()


def test_list_rules_returns_empty_list(rules_api: DistributionRulesApi) -> None:
    rules_api.dictionaries.list_savings_distribution_rules = AsyncMock(return_value=[])

    response = rules_api.client.get("/dictionaries/savings-distribution-rules")

    assert response.status_code == 200
    assert response.json() == []
    rules_api.dictionaries.list_savings_distribution_rules.assert_awaited_once_with()


def test_delete_rule_returns_no_content(
    rule: SimpleNamespace, rules_api: DistributionRulesApi
) -> None:
    rules_api.dictionaries.delete_savings_distribution_rule = AsyncMock(return_value=None)

    response = rules_api.client.delete(f"/dictionaries/savings-distribution-rules/{rule.id}")

    assert response.status_code == 204
    assert response.content == b""
    rules_api.dictionaries.delete_savings_distribution_rule.assert_awaited_once_with(rule.id)
    rules_api.admin_check.assert_called_once_with()


@pytest.mark.parametrize(
    ("method", "action"), [("GET", "get"), ("PUT", "update"), ("DELETE", "delete")]
)
def test_missing_rule_returns_not_found(
    method: str, action: str, rule: SimpleNamespace, rules_api: DistributionRulesApi
) -> None:
    operation = AsyncMock(side_effect=SavingsDistributionRuleNotFoundError(rule.id))
    setattr(rules_api.dictionaries, f"{action}_savings_distribution_rule", operation)

    response = rules_api.client.request(
        method,
        f"/dictionaries/savings-distribution-rules/{rule.id}",
        json=_rule_input(rule) if method == "PUT" else None,
    )

    assert response.status_code == 404
    assert response.json() == {
        "code": "savings_distribution_rule_not_found",
        "context": {"rule_id": str(rule.id)},
    }


@pytest.mark.parametrize("update", [False, True])
@pytest.mark.parametrize(
    ("error_type", "code", "context_key", "expected_status"),
    [
        (CFONotFoundError, "cfo_not_found", "cfo_id", 404),
        (BudgetArticleNotFoundError, "budget_article_not_found", "article_id", 404),
        (MRPNotFoundError, "mrp_not_found", "mrp_id", 404),
        (ArchivedCFOError, "archived_cfo", "cfo_id", 409),
        (ArchivedBudgetArticleError, "archived_budget_article", "article_id", 409),
        (ArchivedMRPError, "archived_mrp", "mrp_id", 409),
        (
            DuplicateSavingsDistributionRuleError,
            "duplicate_savings_distribution_rule",
            "rule_id",
            409,
        ),
    ],
)
def test_rule_write_maps_reference_and_duplicate_errors(
    *,
    update: bool,
    error_type: type[Exception],
    code: str,
    context_key: str,
    expected_status: int,
    rule: SimpleNamespace,
    rules_api: DistributionRulesApi,
) -> None:
    reference_id = uuid4()
    operation = AsyncMock(side_effect=error_type(reference_id))
    action = "update" if update else "create"
    setattr(rules_api.dictionaries, f"{action}_savings_distribution_rule", operation)
    path = "/dictionaries/savings-distribution-rules"

    response = rules_api.client.request(
        "PUT" if update else "POST",
        f"{path}/{rule.id}" if update else path,
        json=_rule_input(rule),
    )

    assert response.status_code == expected_status
    assert response.json() == {"code": code, "context": {context_key: str(reference_id)}}


@pytest.mark.parametrize("update", [False, True])
@pytest.mark.parametrize("field", ["cfo_id", "budget_article_id", "mrp_id"])
@pytest.mark.parametrize("invalid_value", [None, "", "invalid", 42])
def test_rule_write_rejects_invalid_body(
    update: bool,
    field: str,
    invalid_value: object,
    rule: SimpleNamespace,
    rules_api: DistributionRulesApi,
) -> None:
    body: dict[str, object] = dict(_rule_input(rule))
    if invalid_value is None:
        del body[field]
    else:
        body[field] = invalid_value
    path = "/dictionaries/savings-distribution-rules"

    response = rules_api.client.request(
        "PUT" if update else "POST", f"{path}/{rule.id}" if update else path, json=body
    )

    assert response.status_code == 422
    rules_api.dictionaries.create_savings_distribution_rule.assert_not_called()
    rules_api.dictionaries.update_savings_distribution_rule.assert_not_called()


@pytest.mark.parametrize("update", [False, True])
def test_rule_write_rejects_extra_fields(
    update: bool, rule: SimpleNamespace, rules_api: DistributionRulesApi
) -> None:
    path = "/dictionaries/savings-distribution-rules"

    response = rules_api.client.request(
        "PUT" if update else "POST",
        f"{path}/{rule.id}" if update else path,
        json={**_rule_input(rule), "category_id": str(uuid4())},
    )

    assert response.status_code == 422
    rules_api.dictionaries.create_savings_distribution_rule.assert_not_called()
    rules_api.dictionaries.update_savings_distribution_rule.assert_not_called()


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_rule_rejects_invalid_path_id(
    method: str, rule: SimpleNamespace, rules_api: DistributionRulesApi
) -> None:
    response = rules_api.client.request(
        method,
        "/dictionaries/savings-distribution-rules/invalid",
        json=_rule_input(rule) if method == "PUT" else None,
    )

    assert response.status_code == 422
    rules_api.dictionaries.get_savings_distribution_rule.assert_not_called()
    rules_api.dictionaries.update_savings_distribution_rule.assert_not_called()
    rules_api.dictionaries.delete_savings_distribution_rule.assert_not_called()


@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_rule_write_requires_admin(
    method: str, rule: SimpleNamespace, rules_api: DistributionRulesApi
) -> None:
    rules_api.admin_check.side_effect = HTTPException(status_code=403, detail="Forbidden")
    path = "/dictionaries/savings-distribution-rules"

    response = rules_api.client.request(
        method, path if method == "POST" else f"{path}/{rule.id}", json=_rule_input(rule)
    )

    assert response.status_code == 403
    rules_api.dictionaries.create_savings_distribution_rule.assert_not_called()
    rules_api.dictionaries.update_savings_distribution_rule.assert_not_called()
    rules_api.dictionaries.delete_savings_distribution_rule.assert_not_called()
