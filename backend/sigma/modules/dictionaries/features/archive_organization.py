from uuid import UUID

from sigma.modules.dictionaries.domain import Organization
from sigma.modules.dictionaries.repository import OrganizationRepository

from .errors import OrganizationNotFoundError


async def archive_organization(id: UUID, repository: OrganizationRepository) -> Organization:
    organization = await repository.get(id)
    if organization is None:
        raise OrganizationNotFoundError(id)
    if organization.is_archived:
        return organization
    organization.archive()
    await repository.save(organization)
    return organization
