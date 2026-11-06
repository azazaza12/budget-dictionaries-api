import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import (
    CFO,
    MRP,
    ArchivedBudgetArticleError,
    ArchivedCFOError,
    ArchivedMRPError,
    BudgetArticle,
    DictionariesDomainError,
    DistributionRule,
)
from sigma.modules.dictionaries.features.errors import (
    BudgetArticleNotFoundError,
    CFONotFoundError,
    DictionariesFeatureError,
    DistributionRuleNotFoundError,
    DuplicateDistributionRuleError,
    MRPNotFoundError,
)
from sigma.modules.dictionaries.features.update_distribution_rule import (
    update_distribution_rule,
)
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CFORepository,
    DistributionRuleRepository,
    MRPRepository,
)


@pytest.fixture
def rule() -> DistributionRule:
    return DistributionRule(cfo_id=uuid4(), budget_article_id=uuid4(), mrp_id=uuid4())


@pytest.fixture
def references() -> tuple[CFO, BudgetArticle, MRP]:
    return (
        CFO(name="Закупки"),
        BudgetArticle(name="Билеты", category_id=uuid4()),
        MRP(name="Иванов"),
    )


@pytest.fixture
def repositories(
    rule: DistributionRule,
    references: tuple[CFO, BudgetArticle, MRP],
) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    cfo_repository = MagicMock(spec=CFORepository)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    mrp_repository = MagicMock(spec=MRPRepository)
    rule_repository = MagicMock(spec=DistributionRuleRepository)
    for repository, reference in zip(
        (cfo_repository, article_repository, mrp_repository), references, strict=True
    ):
        repository.get = AsyncMock(return_value=reference)
    rule_repository.get = AsyncMock(return_value=rule)
    rule_repository.find_by_pair = AsyncMock(return_value=None)
    rule_repository.save = AsyncMock()
    return cfo_repository, article_repository, mrp_repository, rule_repository


def update_rule(
    rule: DistributionRule,
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> DistributionRule:
    cfo, article, mrp = references
    return asyncio.run(
        update_distribution_rule(
            rule.id,
            cfo.id,
            article.id,
            mrp.id,
            cfo_repository=repositories[0],
            article_repository=repositories[1],
            mrp_repository=repositories[2],
            rule_repository=repositories[3],
        )
    )


def test_update_rule_saves_selected_references(
    rule: DistributionRule,
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> None:
    original_id = rule.id

    result = update_rule(rule, references, repositories)

    assert result is rule
    assert rule.id == original_id
    assert (rule.cfo_id, rule.budget_article_id, rule.mrp_id) == tuple(r.id for r in references)
    repositories[3].get.assert_awaited_once_with(original_id)
    for repository, reference in zip(repositories[:3], references, strict=True):
        repository.get.assert_awaited_once_with(reference.id)
    repositories[3].find_by_pair.assert_awaited_once_with(references[0].id, references[1].id)
    repositories[3].save.assert_awaited_once_with(rule)


def test_update_missing_rule_is_rejected(
    rule: DistributionRule,
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> None:
    repositories[3].get.return_value = None

    with pytest.raises(DistributionRuleNotFoundError) as error:
        update_rule(rule, references, repositories)

    assert error.value.rule_id == rule.id
    assert error.value.code == "savings_distribution_rule_not_found"
    for repository in repositories[:3]:
        repository.get.assert_not_awaited()
    repositories[3].find_by_pair.assert_not_awaited()
    repositories[3].save.assert_not_awaited()


@pytest.mark.parametrize(
    ("reference_index", "error_type"),
    [(0, CFONotFoundError), (1, BudgetArticleNotFoundError), (2, MRPNotFoundError)],
)
def test_update_rule_rejects_missing_reference(
    rule: DistributionRule,
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
    reference_index: int,
    error_type: type[DictionariesFeatureError],
) -> None:
    original_ids = (rule.cfo_id, rule.budget_article_id, rule.mrp_id)
    repositories[reference_index].get.return_value = None

    with pytest.raises(error_type, match=str(references[reference_index].id)):
        update_rule(rule, references, repositories)

    assert (rule.cfo_id, rule.budget_article_id, rule.mrp_id) == original_ids
    repositories[3].find_by_pair.assert_not_awaited()
    repositories[3].save.assert_not_awaited()


def test_update_rule_rejects_conflicting_pair_without_mutation(
    rule: DistributionRule,
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> None:
    original_ids = (rule.cfo_id, rule.budget_article_id, rule.mrp_id)
    existing = DistributionRule(
        cfo_id=references[0].id, budget_article_id=references[1].id, mrp_id=uuid4()
    )
    repositories[3].find_by_pair.return_value = existing

    with pytest.raises(DuplicateDistributionRuleError) as error:
        update_rule(rule, references, repositories)

    assert error.value.rule_id == existing.id
    assert (rule.cfo_id, rule.budget_article_id, rule.mrp_id) == original_ids
    repositories[3].save.assert_not_awaited()


@pytest.mark.parametrize(
    ("reference_index", "error_type"),
    [(0, ArchivedCFOError), (1, ArchivedBudgetArticleError), (2, ArchivedMRPError)],
)
def test_update_rule_rejects_archived_replacement_without_mutation(
    rule: DistributionRule,
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
    reference_index: int,
    error_type: type[DictionariesDomainError],
) -> None:
    original_ids = (rule.cfo_id, rule.budget_article_id, rule.mrp_id)
    references[reference_index].archive()

    with pytest.raises(error_type):
        update_rule(rule, references, repositories)

    assert (rule.cfo_id, rule.budget_article_id, rule.mrp_id) == original_ids
    repositories[3].save.assert_not_awaited()


def test_update_rule_allows_own_pair_and_retains_archived_references(
    rule: DistributionRule,
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> None:
    cfo, article, mrp = references
    rule.cfo_id = cfo.id
    rule.budget_article_id = article.id
    cfo.archive()
    article.archive()
    repositories[3].find_by_pair.return_value = rule

    update_rule(rule, references, repositories)

    assert (rule.cfo_id, rule.budget_article_id, rule.mrp_id) == (cfo.id, article.id, mrp.id)
    repositories[3].save.assert_awaited_once_with(rule)
