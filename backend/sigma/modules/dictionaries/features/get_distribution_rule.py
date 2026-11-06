from uuid import UUID

from sigma.modules.dictionaries.domain import DistributionRule
from sigma.modules.dictionaries.repository import DistributionRuleRepository

from .errors import DistributionRuleNotFoundError


async def get_distribution_rule(
    rule_id: UUID,
    rule_repository: DistributionRuleRepository,
) -> DistributionRule:
    rule = await rule_repository.get(rule_id)
    if rule is None:
        raise DistributionRuleNotFoundError(rule_id)

    return rule
