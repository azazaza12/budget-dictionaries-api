from sigma.modules.dictionaries.domain import Organization
from sigma.modules.dictionaries.repository import OrganizationRepository


async def list_organizations(
    repository: OrganizationRepository, include_archived: bool = False
) -> list[Organization]:
    return await repository.list(include_archived=include_archived)
