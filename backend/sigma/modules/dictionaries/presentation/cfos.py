from uuid import UUID

from fastapi import APIRouter, Depends, status

from .dependencies import DictionariesFacadeDependency, require_dictionaries_admin
from .schemas import CFOInput, CFOView

router = APIRouter(
    prefix="/dictionaries/cfos",
    tags=["dictionaries"],
)


@router.get("")
async def list_cfos(
    dictionaries: DictionariesFacadeDependency,
    include_archived: bool = False,
) -> list[CFOView]:
    cfos = await dictionaries.list_cfos(include_archived=include_archived)
    return [CFOView.model_validate(cfo) for cfo in cfos]


@router.post(
    "", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_dictionaries_admin)]
)
async def create_cfo(data: CFOInput, dictionaries: DictionariesFacadeDependency) -> CFOView:
    cfo = await dictionaries.create_cfo(data.name)
    return CFOView.model_validate(cfo)


@router.put("/{cfo_id}", dependencies=[Depends(require_dictionaries_admin)])
async def rename_cfo(
    cfo_id: UUID, data: CFOInput, dictionaries: DictionariesFacadeDependency
) -> CFOView:
    cfo = await dictionaries.rename_cfo(cfo_id, data.name)
    return CFOView.model_validate(cfo)


@router.post("/{cfo_id}/archive", dependencies=[Depends(require_dictionaries_admin)])
async def archive_cfo(cfo_id: UUID, dictionaries: DictionariesFacadeDependency) -> CFOView:
    cfo = await dictionaries.archive_cfo(cfo_id)
    return CFOView.model_validate(cfo)


@router.post("/{cfo_id}/restore", dependencies=[Depends(require_dictionaries_admin)])
async def restore_cfo(cfo_id: UUID, dictionaries: DictionariesFacadeDependency) -> CFOView:
    cfo = await dictionaries.restore_cfo(cfo_id)
    return CFOView.model_validate(cfo)
