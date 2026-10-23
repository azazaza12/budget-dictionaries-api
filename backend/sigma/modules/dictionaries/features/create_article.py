from uuid import UUID

from sigma.modules.dictionaries.domain import BudgetArticle
from sigma.modules.dictionaries.repository import BudgetArticleRepository, CategoryRepository

from .errors import CategoryNotFoundError, DuplicateDictionaryNameError


async def create_article(
    name: str,
    category_id: UUID,
    category_repository: CategoryRepository,
    article_repository: BudgetArticleRepository,
) -> BudgetArticle:
    category = await category_repository.get(category_id)
    if category is None:
        raise CategoryNotFoundError(category_id)

    article = BudgetArticle.create(name, category)
    if await article_repository.name_exists(article.normalized_name):
        raise DuplicateDictionaryNameError(article.name)

    await article_repository.add(article)
    return article
