from sigma.modules.dictionaries.domain import BudgetArticle
from sigma.modules.dictionaries.repository import BudgetArticleRepository


async def list_articles(
    repository: BudgetArticleRepository, *, include_archived: bool = False
) -> list[BudgetArticle]:
    return await repository.list(include_archived=include_archived)
