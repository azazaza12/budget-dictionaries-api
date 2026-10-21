from uuid import UUID

from sigma.modules.dictionaries.domain import BudgetArticle
from sigma.modules.dictionaries.features.errors import (
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
)
from sigma.modules.dictionaries.repository import BudgetArticleRepository, CategoryRepository


async def restore_article(
    article_id: UUID,
    article_repository: BudgetArticleRepository,
    category_repository: CategoryRepository,
) -> BudgetArticle:
    article = await article_repository.get(article_id)
    if article is None:
        raise BudgetArticleNotFoundError(article_id)
    if not article.is_archived:
        return article

    category = await category_repository.get(article.category_id)
    if category is None:
        raise CategoryNotFoundError(article.category_id)

    article.restore(category)
    await article_repository.save(article)
    return article
