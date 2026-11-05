import asyncio
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sigma.modules.dictionaries.domain import (
    CFO,
    MRP,
    BudgetArticle,
    Category,
    SavingsDistributionRule,
)
from sigma.modules.dictionaries.features.find_mrp_by_savings_distribution_rule import (
    find_mrp_by_savings_distribution_rule,
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
    cfo, article, mrp = references
    cfo_repository = MagicMock(spec=CFORepository)
    article_repository = MagicMock(spec=BudgetArticleRepository)
    mrp_repository = MagicMock(spec=MRPRepository)
    rule_repository = MagicMock(spec=SavingsDistributionRuleRepository)
    for repository, reference in zip(
        (cfo_repository, article_repository, mrp_repository), references, strict=True
    ):
        repository.get = AsyncMock(return_value=reference)
    rule_repository.find_by_pair = AsyncMock(
        return_value=SavingsDistributionRule(
            cfo_id=cfo.id, budget_article_id=article.id, mrp_id=mrp.id
        )
    )
    return cfo_repository, article_repository, mrp_repository, rule_repository


def test_find_mrp_returns_mrp_when_all_references_are_active(
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> None:
    cfo, article, mrp = references

    result = asyncio.run(
        find_mrp_by_savings_distribution_rule(
            cfo.id,
            article.id,
            cfo_repository=repositories[0],
            article_repository=repositories[1],
            mrp_repository=repositories[2],
            rule_repository=repositories[3],
        )
    )

    assert result is mrp
    repositories[3].find_by_pair.assert_awaited_once_with(cfo.id, article.id)
    for repository, reference in zip(repositories[:3], references, strict=True):
        repository.get.assert_awaited_once_with(reference.id)
    for repository in repositories:
        repository.add.assert_not_called()
        repository.save.assert_not_called()
    repositories[3].delete.assert_not_called()


def test_find_mrp_returns_none_without_rule(
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
) -> None:
    cfo, article, _ = references
    repositories[3].find_by_pair.return_value = None

    result = asyncio.run(
        find_mrp_by_savings_distribution_rule(
            cfo.id,
            article.id,
            cfo_repository=repositories[0],
            article_repository=repositories[1],
            mrp_repository=repositories[2],
            rule_repository=repositories[3],
        )
    )

    assert result is None
    repositories[3].find_by_pair.assert_awaited_once_with(cfo.id, article.id)
    for repository in repositories[:3]:
        repository.get.assert_not_awaited()


@pytest.mark.parametrize("reference_index", [0, 1, 2])
@pytest.mark.parametrize("missing", [False, True])
def test_find_mrp_returns_none_for_archived_or_missing_reference(
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
    reference_index: int,
    missing: bool,
) -> None:
    cfo, article, _ = references
    if missing:
        repositories[reference_index].get.return_value = None
    else:
        references[reference_index].archive()

    result = asyncio.run(
        find_mrp_by_savings_distribution_rule(
            cfo.id,
            article.id,
            cfo_repository=repositories[0],
            article_repository=repositories[1],
            mrp_repository=repositories[2],
            rule_repository=repositories[3],
        )
    )

    assert result is None
    repositories[3].find_by_pair.assert_awaited_once_with(cfo.id, article.id)
    repositories[reference_index].get.assert_awaited_once_with(references[reference_index].id)
    for repository in repositories[reference_index + 1 : 3]:
        repository.get.assert_not_awaited()


@pytest.mark.parametrize("reference_index", [0, 1, 2])
def test_find_mrp_returns_mrp_after_reference_is_restored(
    references: tuple[CFO, BudgetArticle, MRP],
    repositories: tuple[MagicMock, MagicMock, MagicMock, MagicMock],
    reference_index: int,
) -> None:
    cfo, article, mrp = references
    references[reference_index].archive()

    async def find() -> MRP | None:
        return await find_mrp_by_savings_distribution_rule(
            cfo.id,
            article.id,
            cfo_repository=repositories[0],
            article_repository=repositories[1],
            mrp_repository=repositories[2],
            rule_repository=repositories[3],
        )

    assert asyncio.run(find()) is None
    reference = references[reference_index]
    if isinstance(reference, BudgetArticle):
        reference.restore(Category(id=reference.category_id, name="Командировки"))
    else:
        reference.restore()
    assert asyncio.run(find()) is mrp
