from uuid import UUID

from fastapi import APIRouter, status
from fastapi.params import Depends

from .dependencies import DictionariesFacadeDependency, require_dictionaries_admin
from .schemas import OrganizationInput, OrganizationView

router = APIRouter(prefix="/dictionaries/organizations", tags=["dictionaries"])


@router.post(
    "", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_dictionaries_admin)]
)
async def create_organization(
    data: OrganizationInput, dictionaries: DictionariesFacadeDependency
) -> OrganizationView:
    organization = await dictionaries.create_organization(data.name, data.external_name)
    return OrganizationView.model_validate(organization)


@router.post("/{organization_id}/archive", dependencies=[Depends(require_dictionaries_admin)])
async def archive_organization(
    organization_id: UUID, dictionaries: DictionariesFacadeDependency
) -> OrganizationView:
    organization = await dictionaries.archive_organization(organization_id)
    return OrganizationView.model_validate(organization)


@router.post("/{organization_id}/restore", dependencies=[Depends(require_dictionaries_admin)])
async def restore_organization(
    organization_id: UUID, dictionaries: DictionariesFacadeDependency
) -> OrganizationView:
    organization = await dictionaries.restore_organization(organization_id)
    return OrganizationView.model_validate(organization)


@router.get("")
async def list_organizations(
    dictionaries: DictionariesFacadeDependency, include_archived: bool = False
) -> list[OrganizationView]:
    organizations = await dictionaries.list_organizations(include_archived=include_archived)
    return [OrganizationView.model_validate(organization) for organization in organizations]


@router.put("/{organization_id}", dependencies=[Depends(require_dictionaries_admin)])
async def rename_organization(
    organization_id: UUID, data: OrganizationInput, dictionaries: DictionariesFacadeDependency
) -> OrganizationView:
    organization = await dictionaries.rename_organization(
        organization_id, data.name, data.external_name
    )
    return OrganizationView.model_validate(organization)
