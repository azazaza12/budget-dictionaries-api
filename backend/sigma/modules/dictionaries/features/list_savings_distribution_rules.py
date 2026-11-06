from sigma.modules.dictionaries.repository import (
    SavingsDistributionRuleDetails,
    SavingsDistributionRuleRepository,
)


async def list_savings_distribution_rules(
    rule_repository: SavingsDistributionRuleRepository,
) -> list[SavingsDistributionRuleDetails]:
    return await rule_repository.list()
