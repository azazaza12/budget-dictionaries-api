from uuid import UUID

from sigma.modules.dictionaries.domain import Organization, normalize_external_name, normalize_name
from sigma.modules.dictionaries.repository import OrganizationRepository

from .errors import (
    DuplicateDictionaryNameError,
    DuplicateOrganizationExternalNameError,
    OrganizationNotFoundError,
)


async def rename_organization(
    id: UUID, new_name: str, new_external_name: str, repository: OrganizationRepository
) -> Organization:
    organization = await repository.get(id)
    if organization is None:
        raise OrganizationNotFoundError(id)
    normalized_name = normalize_name(new_name)
    if await repository.name_exists(normalized_name, exclude_id=id):
        raise DuplicateDictionaryNameError(new_name)
    normalized_external_name = normalize_external_name(new_external_name)
    if await repository.external_name_exists(normalized_external_name, exclude_id=id):
        raise DuplicateOrganizationExternalNameError(new_external_name)

    organization.rename(new_name)
    organization.rename_external_name(new_external_name)
    await repository.save(organization)
    return organization
