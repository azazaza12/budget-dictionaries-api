from sigma.modules.dictionaries.domain import Category
from sigma.modules.dictionaries.features.errors import DuplicateDictionaryNameError
from sigma.modules.dictionaries.repository import CategoryRepository


async def create_category(name: str, repository: CategoryRepository) -> Category:
    category = Category(name=name)
    if await repository.name_exists(category.normalized_name):
        raise DuplicateDictionaryNameError(category.name)
    await repository.add(category)
    return category
