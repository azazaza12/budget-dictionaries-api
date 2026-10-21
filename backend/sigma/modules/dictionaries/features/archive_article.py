from uuid import UUID

from sigma.modules.dictionaries.domain import BudgetArticle
from sigma.modules.dictionaries.features.errors import BudgetArticleNotFoundError
from sigma.modules.dictionaries.repository import BudgetArticleRepository


async def archive_article(article_id: UUID, repository: BudgetArticleRepository) -> BudgetArticle:
    article = await repository.get(article_id)
    if article is None:
        raise BudgetArticleNotFoundError(article_id)
    if article.is_archived:
        return article
    article.archive()
    await repository.save(article)
    return article
