from uuid import UUID

from sigma.modules.dictionaries.repository import DistributionRuleRepository

from .errors import DistributionRuleNotFoundError


async def delete_distribution_rule(
    rule_id: UUID,
    rule_repository: DistributionRuleRepository,
) -> None:
    rule = await rule_repository.get(rule_id)
    if rule is None:
        raise DistributionRuleNotFoundError(rule_id)

    await rule_repository.delete(rule)
