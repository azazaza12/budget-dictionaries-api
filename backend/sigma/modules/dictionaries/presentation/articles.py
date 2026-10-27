from uuid import UUID

from fastapi import APIRouter, Depends, status

from .dependencies import DictionariesFacadeDependency, require_dictionaries_admin
from .schemas import (
    BudgetArticleCategoryInput,
    BudgetArticleInput,
    BudgetArticleNameInput,
    BudgetArticleView,
)

router = APIRouter(prefix="/dictionaries/articles", tags=["dictionaries"])


@router.get("")
async def list_articles(
    dictionaries: DictionariesFacadeDependency,
    include_archived: bool = False,
) -> list[BudgetArticleView]:
    articles = await dictionaries.list_articles(include_archived=include_archived)
    return [BudgetArticleView.model_validate(article) for article in articles]


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_dictionaries_admin)],
)
async def create_article(
    data: BudgetArticleInput,
    dictionaries: DictionariesFacadeDependency,
) -> BudgetArticleView:
    article = await dictionaries.create_article(data.name, data.category_id)
    return BudgetArticleView.model_validate(article)


@router.put(
    "/{article_id}",
    dependencies=[Depends(require_dictionaries_admin)],
)
async def rename_article(
    article_id: UUID,
    data: BudgetArticleNameInput,
    dictionaries: DictionariesFacadeDependency,
) -> BudgetArticleView:
    article = await dictionaries.rename_article(article_id, data.name)
    return BudgetArticleView.model_validate(article)


@router.put(
    "/{article_id}/category",
    dependencies=[Depends(require_dictionaries_admin)],
)
async def move_article(
    article_id: UUID,
    data: BudgetArticleCategoryInput,
    dictionaries: DictionariesFacadeDependency,
) -> BudgetArticleView:
    article = await dictionaries.move_article(article_id, data.category_id)
    return BudgetArticleView.model_validate(article)


@router.post(
    "/{article_id}/archive",
    dependencies=[Depends(require_dictionaries_admin)],
)
async def archive_article(
    article_id: UUID,
    dictionaries: DictionariesFacadeDependency,
) -> BudgetArticleView:
    article = await dictionaries.archive_article(article_id)
    return BudgetArticleView.model_validate(article)


@router.post(
    "/{article_id}/restore",
    dependencies=[Depends(require_dictionaries_admin)],
)
async def restore_article(
    article_id: UUID,
    dictionaries: DictionariesFacadeDependency,
) -> BudgetArticleView:
    article = await dictionaries.restore_article(article_id)
    return BudgetArticleView.model_validate(article)
