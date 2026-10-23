from sigma.modules.dictionaries.domain import Category
from sigma.modules.dictionaries.repository import CategoryRepository


async def list_categories(
    repository: CategoryRepository,
    *,
    include_archived: bool = False,
) -> list[Category]:
    return await repository.list(include_archived=include_archived)
