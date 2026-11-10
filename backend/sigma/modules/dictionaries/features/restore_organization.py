from uuid import UUID

from sigma.modules.dictionaries.domain import Organization
from sigma.modules.dictionaries.repository import OrganizationRepository

from .errors import OrganizationNotFoundError


async def restore_organization(id: UUID, repository: OrganizationRepository) -> Organization:
    organization = await repository.get(id)
    if organization is None:
        raise OrganizationNotFoundError(id)
    if not organization.is_archived:
        return organization
    organization.restore()
    await repository.save(organization)
    return organization
