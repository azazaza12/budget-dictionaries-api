from sigma.modules.dictionaries.domain import Category
from sigma.modules.dictionaries.repository import CategoryRepository

from .errors import DuplicateDictionaryNameError


async def create_category(name: str, repository: CategoryRepository) -> Category:
    category = Category(name=name)
    if await repository.name_exists(category.normalized_name):
        raise DuplicateDictionaryNameError(category.name)
    await repository.add(category)
    return category
