from uuid import UUID

from sigma.modules.dictionaries.domain import BudgetArticle
from sigma.modules.dictionaries.features.errors import (
    BudgetArticleNotFoundError,
    CategoryNotFoundError,
)
from sigma.modules.dictionaries.repository import (
    BudgetArticleRepository,
    CategoryRepository,
)


async def move_article(
    article_id: UUID,
    target_category_id: UUID,
    article_repository: BudgetArticleRepository,
    category_repository: CategoryRepository,
) -> BudgetArticle:
    article = await article_repository.get(article_id)
    if article is None:
        raise BudgetArticleNotFoundError(article_id)

    target_category = await category_repository.get(target_category_id)
    if target_category is None:
        raise CategoryNotFoundError(target_category_id)

    article.move_to(target_category)
    await article_repository.save(article)
    return article
