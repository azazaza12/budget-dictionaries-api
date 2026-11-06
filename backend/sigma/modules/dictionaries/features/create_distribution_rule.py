from uuid import UUID

from sigma.modules.dictionaries.domain import DistributionRule
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CFORepository,
    DistributionRuleRepository,
    MRPRepository,
)

from .errors import (
    BudgetArticleNotFoundError,
    CFONotFoundError,
    DuplicateDistributionRuleError,
    MRPNotFoundError,
)


async def create_distribution_rule(
    cfo_id: UUID,
    budget_article_id: UUID,
    mrp_id: UUID,
    *,
    cfo_repository: CFORepository,
    article_repository: BudgetArticleRepository,
    mrp_repository: MRPRepository,
    rule_repository: DistributionRuleRepository,
) -> DistributionRule:
    cfo = await cfo_repository.get(cfo_id)
    if cfo is None:
        raise CFONotFoundError(cfo_id)

    article = await article_repository.get(budget_article_id)
    if article is None:
        raise BudgetArticleNotFoundError(budget_article_id)

    mrp = await mrp_repository.get(mrp_id)
    if mrp is None:
        raise MRPNotFoundError(mrp_id)

    rule = DistributionRule.create(cfo, article, mrp)
    existing = await rule_repository.find_by_pair(cfo_id, budget_article_id)
    if existing is not None:
        raise DuplicateDistributionRuleError(existing.id)

    await rule_repository.add(rule)
    return rule
