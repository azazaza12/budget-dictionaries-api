from uuid import UUID

from sigma.modules.dictionaries.domain import Category
from sigma.modules.dictionaries.features.errors import CategoryNotFoundError
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CategoryRepository,
)


async def archive_category(
    category_id: UUID,
    category_repository: CategoryRepository,
    article_repository: BudgetArticleRepository,
) -> Category:
    category = await category_repository.get(category_id)
    if category is None:
        raise CategoryNotFoundError(category_id)
    if category.is_archived:
        return category

    articles = await article_repository.list_by_category(category_id)
    category.archive()
    for article in articles:
        article.archive()

    await category_repository.save(category)
    for article in articles:
        await article_repository.save(article)

    return category
