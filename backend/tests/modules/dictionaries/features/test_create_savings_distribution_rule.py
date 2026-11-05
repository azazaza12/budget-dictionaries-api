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
    SavingsDistributionRule,
)
from sigma.modules.dictionaries.features.create_savings_distribution_rule import (
    create_savings_distribution_rule,
)
from sigma.modules.dictionaries.features.errors import (
    BudgetArticleNotFoundError,
    CFONotFoundError,
    DictionariesFeatureError,
    DuplicateSavingsDistributionRuleError,
    MRPNotFoundError,
)
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CFORepository,
    MRPRepository,
    SavingsDistributionRuleRepository,
)


@pytest.fixture
def references() -> tuple[CFO, BudgetArticle, MRP]:
    return (
        CFO(name="Закупки"),
        BudgetArticle(name="Билеты", category_id=uuid4()),
        MRP(name="Иванов"),
    )


@pytest.fixture
def repositories(
    references: tuple[CFO, BudgetArticle, MRP],
) -> tuple[MagicMock, MagicMock, MagicMock, MagicMock]:
    cfo_repository = MagicMock(spec=CFORepository)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    mrp_repository = MagicMock(spec=MRPRepository)
    rule_repository = MagicMock(spec=SavingsDistributionRuleRepository)
    for repository, reference in zip(
        (cfo_repository, article_repository, mrp_repository), references, strict=True
    ):
        repository.get = AsyncMock(return_value=reference)
    rule_repository.find_by_pair = AsyncMock(return_value=None)
    rule_repository.add = AsyncMock()
    return cfo_repository, article_repository, mrp_repository, rule_repository


def test_create_rule_saves_rule_with_selected_references(
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> None:
    cfo, article, mrp = references

    rule = asyncio.run(
        create_savings_distribution_rule(
            cfo.id,
            article.id,
            mrp.id,
            cfo_repository=repositories[0],
            article_repository=repositories[1],
            mrp_repository=repositories[2],
            rule_repository=repositories[3],
        )
    )

    assert (rule.cfo_id, rule.budget_article_id, rule.mrp_id) == (cfo.id, article.id, mrp.id)
    for repository, reference in zip(repositories[:3], references, strict=True):
        repository.get.assert_awaited_once_with(reference.id)
    repositories[3].find_by_pair.assert_awaited_once_with(cfo.id, article.id)
    repositories[3].add.assert_awaited_once_with(rule)


@pytest.mark.parametrize(
    ("reference_index", "error_type"),
    [(0, CFONotFoundError), (1, BudgetArticleNotFoundError), (2, MRPNotFoundError)],
)
def test_create_rule_rejects_missing_reference(
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
    reference_index: int,
    error_type: type[DictionariesFeatureError],
) -> None:
    cfo, article, mrp = references
    repositories[reference_index].get.return_value = None

    with pytest.raises(error_type, match=str(references[reference_index].id)):
        asyncio.run(
            create_savings_distribution_rule(
                cfo.id,
                article.id,
                mrp.id,
                cfo_repository=repositories[0],
                article_repository=repositories[1],
                mrp_repository=repositories[2],
                rule_repository=repositories[3],
            )
        )

    repositories[3].find_by_pair.assert_not_awaited()
    repositories[3].add.assert_not_awaited()


@pytest.mark.parametrize(
    ("reference_index", "error_type"),
    [(0, ArchivedCFOError), (1, ArchivedBudgetArticleError), (2, ArchivedMRPError)],
)
def test_create_rule_rejects_archived_reference(
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
    reference_index: int,
    error_type: type[DictionariesDomainError],
) -> None:
    cfo, article, mrp = references
    references[reference_index].archive()

    with pytest.raises(error_type, match=str(references[reference_index].id)):
        asyncio.run(
            create_savings_distribution_rule(
                cfo.id,
                article.id,
                mrp.id,
                cfo_repository=repositories[0],
                article_repository=repositories[1],
                mrp_repository=repositories[2],
                rule_repository=repositories[3],
            )
        )

    repositories[3].find_by_pair.assert_not_awaited()
    repositories[3].add.assert_not_awaited()


@pytest.mark.parametrize("same_mrp", [False, True])
def test_create_rule_rejects_duplicate_pair_with_existing_rule_id(
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
    same_mrp: bool,
) -> None:
    cfo, article, mrp = references
    existing_mrp_id = mrp.id if same_mrp else uuid4()
    existing = SavingsDistributionRule(
        cfo_id=cfo.id, budget_article_id=article.id, mrp_id=existing_mrp_id
    )
    repositories[3].find_by_pair.return_value = existing

    with pytest.raises(DuplicateSavingsDistributionRuleError) as error:
        asyncio.run(
            create_savings_distribution_rule(
                cfo.id,
                article.id,
                mrp.id,
                cfo_repository=repositories[0],
                article_repository=repositories[1],
                mrp_repository=repositories[2],
                rule_repository=repositories[3],
            )
        )

    assert error.value.rule_id == existing.id
    assert error.value.code == "duplicate_savings_distribution_rule"
    repositories[3].find_by_pair.assert_awaited_once_with(cfo.id, article.id)
    repositories[3].add.assert_not_awaited()
    assert existing.mrp_id == existing_mrp_id
