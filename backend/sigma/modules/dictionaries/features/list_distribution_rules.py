from sigma.modules.dictionaries.repository import (
    DistributionRuleDetails,
    DistributionRuleRepository,
)


async def list_distribution_rules(
    rule_repository: DistributionRuleRepository,
) -> list[DistributionRuleDetails]:
    return await rule_repository.list()
