from uuid import UUID

from sigma.modules.dictionaries.domain import SavingsDistributionRule
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CFORepository,
    MRPRepository,
    SavingsDistributionRuleRepository,
)

from .errors import (
    BudgetArticleNotFoundError,
    CFONotFoundError,
    DuplicateSavingsDistributionRuleError,
    MRPNotFoundError,
)


async def create_savings_distribution_rule(
    cfo_id: UUID,
    budget_article_id: UUID,
    mrp_id: UUID,
    *,
    cfo_repository: CFORepository,
    article_repository: BudgetArticleRepository,
    mrp_repository: MRPRepository,
    rule_repository: SavingsDistributionRuleRepository,
) -> SavingsDistributionRule:
    cfo = await cfo_repository.get(cfo_id)
    if cfo is None:
        raise CFONotFoundError(cfo_id)

    article = await article_repository.get(budget_article_id)
    if article is None:
        raise BudgetArticleNotFoundError(budget_article_id)

    mrp = await mrp_repository.get(mrp_id)
    if mrp is None:
        raise MRPNotFoundError(mrp_id)

    rule = SavingsDistributionRule.create(cfo, article, mrp)
    existing = await rule_repository.find_by_pair(cfo_id, budget_article_id)
    if existing is not None:
        raise DuplicateSavingsDistributionRuleError(existing.id)

    await rule_repository.add(rule)
    return rule
