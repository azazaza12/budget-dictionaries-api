from uuid import UUID

from sigma.modules.dictionaries.domain import SavingsDistributionRule
from sigma.modules.dictionaries.repository import SavingsDistributionRuleRepository

from .errors import SavingsDistributionRuleNotFoundError


async def get_savings_distribution_rule(
    rule_id: UUID,
    rule_repository: SavingsDistributionRuleRepository,
) -> SavingsDistributionRule:
    rule = await rule_repository.get(rule_id)
    if rule is None:
        raise SavingsDistributionRuleNotFoundError(rule_id)

    return rule
