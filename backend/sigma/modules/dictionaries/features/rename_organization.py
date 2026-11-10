from uuid import UUID

from sigma.modules.dictionaries.domain import Organization, normalize_1c_name, normalize_name
from sigma.modules.dictionaries.repository import OrganizationRepository

from .errors import (
    DuplicateDictionaryNameError,
    DuplicateOrganizationNameIn1CError,
    OrganizationNotFoundError,
)


async def rename_organization(
    id: UUID, new_name: str, new_name_in_1c: str, repository: OrganizationRepository
) -> Organization:
    organization = await repository.get(id)
    if organization is None:
        raise OrganizationNotFoundError(id)
    normalized_name = normalize_name(new_name)
    if await repository.name_exists(normalized_name, exclude_id=id):
        raise DuplicateDictionaryNameError(new_name)
    normalized_name_in_1c = normalize_1c_name(new_name_in_1c)
    if await repository.name_in_1c_exists(normalized_name_in_1c, exclude_id=id):
        raise DuplicateOrganizationNameIn1CError(new_name_in_1c)

    organization.rename(new_name)
    organization.rename_in_1c(new_name_in_1c)
    await repository.save(organization)
    return organization
