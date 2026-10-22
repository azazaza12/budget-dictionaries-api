from uuid import UUID

from fastapi import APIRouter, Depends, status

from .dependencies import DictionariesFacadeDependency, require_dictionaries_admin
from .schemas import CategoryInput, CategoryView

router = APIRouter(
    prefix="/dictionaries/categories",
    tags=["dictionaries"],
)


@router.get("")
async def list_categories(
    dictionaries: DictionariesFacadeDependency,
    include_archived: bool = False,
) -> list[CategoryView]:
    categories = await dictionaries.list_categories(include_archived=include_archived)
    return [CategoryView.model_validate(category) for category in categories]


@router.post(
    "", status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_dictionaries_admin)]
)
async def create_category(
    data: CategoryInput,
    dictionaries: DictionariesFacadeDependency,
) -> CategoryView:
    category = await dictionaries.create_category(data.name)
    return CategoryView.model_validate(category)


@router.post("/{category_id}/restore", dependencies=[Depends(require_dictionaries_admin)])
async def restore_category(
    category_id: UUID, dictionaries: DictionariesFacadeDependency
) -> CategoryView:
    category = await dictionaries.restore_category(category_id)
    return CategoryView.model_validate(category)


@router.post("/{category_id}/archive", dependencies=[Depends(require_dictionaries_admin)])
async def archive_category(
    category_id: UUID, dictionaries: DictionariesFacadeDependency
) -> CategoryView:
    category = await dictionaries.archive_category(category_id)
    return CategoryView.model_validate(category)


@router.put("/{category_id}", dependencies=[Depends(require_dictionaries_admin)])
async def rename_category(
    category_id: UUID, data: CategoryInput, dictionaries: DictionariesFacadeDependency
) -> CategoryView:
    category = await dictionaries.rename_category(category_id, data.name)
    return CategoryView.model_validate(category)
