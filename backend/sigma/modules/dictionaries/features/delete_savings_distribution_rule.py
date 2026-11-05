from uuid import UUID

from sigma.modules.dictionaries.repository import SavingsDistributionRuleRepository

from .errors import SavingsDistributionRuleNotFoundError


async def delete_savings_distribution_rule(
    rule_id: UUID,
    rule_repository: SavingsDistributionRuleRepository,
) -> None:
    rule = await rule_repository.get(rule_id)
    if rule is None:
        raise SavingsDistributionRuleNotFoundError(rule_id)

    await rule_repository.delete(rule)
