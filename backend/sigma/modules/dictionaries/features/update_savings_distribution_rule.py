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
    SavingsDistributionRuleNotFoundError,
)


async def update_savings_distribution_rule(
    rule_id: UUID,
    cfo_id: UUID,
    budget_article_id: UUID,
    mrp_id: UUID,
    *,
    cfo_repository: CFORepository,
    article_repository: BudgetArticleRepository,
    mrp_repository: MRPRepository,
    rule_repository: SavingsDistributionRuleRepository,
) -> SavingsDistributionRule:
    rule = await rule_repository.get(rule_id)
    if rule is None:
        raise SavingsDistributionRuleNotFoundError(rule_id)

    cfo = await cfo_repository.get(cfo_id)
    if cfo is None:
        raise CFONotFoundError(cfo_id)

    article = await article_repository.get(budget_article_id)
    if article is None:
        raise BudgetArticleNotFoundError(budget_article_id)

    mrp = await mrp_repository.get(mrp_id)
    if mrp is None:
        raise MRPNotFoundError(mrp_id)

    existing = await rule_repository.find_by_pair(cfo_id, budget_article_id)
    if existing is not None and existing.id != rule.id:
        raise DuplicateSavingsDistributionRuleError(existing.id)

    rule.update(cfo, article, mrp)
    await rule_repository.save(rule)
    return rule
