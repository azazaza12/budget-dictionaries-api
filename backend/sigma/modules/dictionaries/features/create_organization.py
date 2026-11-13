from sigma.modules.dictionaries.domain import Organization
from sigma.modules.dictionaries.repository import OrganizationRepository

from .errors import DuplicateDictionaryNameError, DuplicateOrganizationExternalNameError


async def create_organization(
    name: str, external_name: str, repository: OrganizationRepository
) -> Organization:
    organization = Organization(name=name, external_name=external_name)
    if await repository.name_exists(organization.normalized_name):
        raise DuplicateDictionaryNameError(organization.name)
    if await repository.external_name_exists(organization.normalized_external_name):
        raise DuplicateOrganizationExternalNameError(organization.external_name)
    await repository.add(organization)
    return organization
