from sigma.modules.dictionaries.repository import (
    SavingsDistributionRuleListItem,
    SavingsDistributionRuleRepository,
)


async def list_savings_distribution_rules(
    rule_repository: SavingsDistributionRuleRepository,
) -> list[SavingsDistributionRuleListItem]:
    return await rule_repository.list()
