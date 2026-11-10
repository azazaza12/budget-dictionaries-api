from sigma.modules.dictionaries.domain import Organization
from sigma.modules.dictionaries.repository import OrganizationRepository

from .errors import DuplicateDictionaryNameError, DuplicateOrganizationNameIn1CError


async def create_organization(
    name: str, name_in_1c: str, repository: OrganizationRepository
) -> Organization:
    organization = Organization(name=name, name_in_1c=name_in_1c)
    if await repository.name_exists(organization.normalized_name):
        raise DuplicateDictionaryNameError(organization.name)
    if await repository.name_in_1c_exists(organization.normalized_name_in_1c):
        raise DuplicateOrganizationNameIn1CError(organization.name_in_1c)
    await repository.add(organization)
    return organization
