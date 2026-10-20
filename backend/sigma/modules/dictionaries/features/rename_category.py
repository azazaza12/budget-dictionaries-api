from uuid import UUID

from sigma.modules.dictionaries.domain import Category, normalize_name
from sigma.modules.dictionaries.features.errors import (
    CategoryNotFoundError,
    DuplicateDictionaryNameError,
)
from sigma.modules.dictionaries.repository import CategoryRepository


async def rename_category(
    category_id: UUID,
    new_name: str,
    repository: CategoryRepository,
) -> Category:
    category = await repository.get(category_id)
    if category is None:
        raise CategoryNotFoundError(category_id)

    normalized_name = normalize_name(new_name)
    if await repository.name_exists(normalized_name, exclude_id=category_id):
        raise DuplicateDictionaryNameError(new_name)

    category.rename(new_name)
    await repository.save(category)
    return category
