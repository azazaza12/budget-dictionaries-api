from uuid import UUID

from sigma.modules.dictionaries.domain import Category
from sigma.modules.dictionaries.features.errors import CategoryNotFoundError
from sigma.modules.dictionaries.repository import CategoryRepository


async def restore_category(
    category_id: UUID,
    repository: CategoryRepository,
) -> Category:
    category = await repository.get(category_id)
    if category is None:
        raise CategoryNotFoundError(category_id)
    if not category.is_archived:
        return category

    category.restore()
    await repository.save(category)
    return category
