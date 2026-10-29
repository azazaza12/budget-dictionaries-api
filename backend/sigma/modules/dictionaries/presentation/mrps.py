from uuid import UUID

from fastapi import APIRouter, Depends, status

from .dependencies import DictionariesFacadeDependency, require_dictionaries_admin
from .schemas import MRPInput, MRPView

router = APIRouter(
    prefix="/dictionaries/mrps",
    tags=["dictionaries"],
)


@router.get("")
async def list_mrps(
    dictionaries: DictionariesFacadeDependency,
    include_archived: bool = False,
) -> list[MRPView]:
    mrps = await dictionaries.list_mrps(include_archived=include_archived)
    return [MRPView.model_validate(mrp) for mrp in mrps]


@router.post(
    "", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_dictionaries_admin)]
)
async def create_mrp(data: MRPInput, dictionaries: DictionariesFacadeDependency) -> MRPView:
    mrp = await dictionaries.create_mrp(data.name)
    return MRPView.model_validate(mrp)


@router.put("/{mrp_id}", dependencies=[Depends(require_dictionaries_admin)])
async def rename_mrp(
    mrp_id: UUID, data: MRPInput, dictionaries: DictionariesFacadeDependency
) -> MRPView:
    mrp = await dictionaries.rename_mrp(mrp_id, data.name)
    return MRPView.model_validate(mrp)


@router.post("/{mrp_id}/archive", dependencies=[Depends(require_dictionaries_admin)])
async def archive_mrp(mrp_id: UUID, dictionaries: DictionariesFacadeDependency) -> MRPView:
    mrp = await dictionaries.archive_mrp(mrp_id)
    return MRPView.model_validate(mrp)


@router.post("/{mrp_id}/restore", dependencies=[Depends(require_dictionaries_admin)])
async def restore_mrp(mrp_id: UUID, dictionaries: DictionariesFacadeDependency) -> MRPView:
    mrp = await dictionaries.restore_mrp(mrp_id)
    return MRPView.model_validate(mrp)
