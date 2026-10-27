from uuid import UUID

from sigma.modules.dictionaries.domain import BudgetArticle, normalize_name
from sigma.modules.dictionaries.repository import BudgetArticleRepository

from .errors import BudgetArticleNotFoundError, DuplicateDictionaryNameError


async def rename_article(
    article_id: UUID,
    new_name: str,
    repository: BudgetArticleRepository,
) -> BudgetArticle:
    article = await repository.get(article_id)
    if article is None:
        raise BudgetArticleNotFoundError(article_id)

    normalized_name = normalize_name(new_name)
    if await repository.name_exists(normalized_name, exclude_id=article_id):
        raise DuplicateDictionaryNameError(new_name)

    article.rename(new_name)
    await repository.save(article)
    return article
