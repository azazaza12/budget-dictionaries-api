from uuid import UUID

from sigma.modules.dictionaries.domain import MRP
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CFORepository,
    MRPRepository,
    SavingsDistributionRuleRepository,
)


async def find_mrp_by_savings_distribution_rule(
    cfo_id: UUID,
    budget_article_id: UUID,
    *,
    cfo_repository: CFORepository,
    article_repository: BudgetArticleRepository,
    mrp_repository: MRPRepository,
    rule_repository: SavingsDistributionRuleRepository,
) -> MRP | None:
    rule = await rule_repository.find_by_pair(cfo_id, budget_article_id)
    if rule is None:
        return None

    cfo = await cfo_repository.get(rule.cfo_id)
    if cfo is None or cfo.is_archived:
        return None

    article = await article_repository.get(rule.budget_article_id)
    if article is None or article.is_archived:
        return None

    mrp = await mrp_repository.get(rule.mrp_id)
    if mrp is None or mrp.is_archived:
        return None

    return mrp
